"""Novas operações independentes da API CorelDRAW, com resultados DXF novos.

Não representa implementação do eCut. Geometria plana conservadora;
nenhuma rotina altera ou sobrescreve arquivos-fonte.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

import ezdxf
from ezdxf import bbox
from ezdxf.math import Matrix44
from shapely.geometry import Polygon, Point, box
from shapely.affinity import rotate, translate

from laser_core import safe_output, _load, _flat_xy

EPS = 1e-7
MAX_PIECES = 60


@dataclass
class TrueNestResult:
    output: Path
    piece_count: int
    utilization_percent: float
    sheet_width: float
    sheet_height: float
    note: str


def _to_polygon(e, circle_segments=96):
    """Represente contornos com fidelidade limitada; rejeite arcos de polilinhas.

    Transformações finais preservam a entidade original (inclusive círculo),
    não transformam círculo em polígono simplificado para exportação.
    """
    if not _flat_xy(e):
        raise ValueError('Contorno com extrusão não planar não aceito.')
    if e.dxftype() == 'CIRCLE':
        c=e.dxf.center
        if abs(float(c.z)) > EPS: raise ValueError('Somente círculos no plano z=0.')
        r=float(e.dxf.radius)
        if r<=EPS: raise ValueError('Círculo de raio inválido.')
        # Polígono CIRCUNSCRITO: evitar colisões ocultas por aproximação do círculo.
        outer_radius=r / math.cos(math.pi / circle_segments)
        return Point(float(c.x), float(c.y)).buffer(outer_radius, quad_segs=circle_segments//4)
    if e.dxftype()=='LWPOLYLINE':
        if not e.closed or e.has_arc or e.has_width:
            raise ValueError('Nesting real requer polilinhas fechadas sem arco/bulge ou largura.')
        if abs(float(e.dxf.get('elevation', 0))) > EPS:
            raise ValueError('Somente polilinhas no plano z=0.')
        pts=[(float(x),float(y)) for x,y in e.get_points('xy')]
    elif e.dxftype()=='POLYLINE' and e.is_2d_polyline:
        if not e.is_closed or any(abs(float(v.dxf.get('bulge',0)))>EPS or
            abs(float(v.dxf.get('start_width',0)))>EPS or abs(float(v.dxf.get('end_width',0)))>EPS
            for v in e.vertices):
            raise ValueError('Polilinhas POLYLINE devem ser fechadas, retas e sem largura.')
        pts=[]
        for v in e.vertices:
            xyz=v.dxf.location
            if abs(float(xyz.z)) > EPS: raise ValueError('Somente polilinhas no plano z=0.')
            pts.append((float(xyz.x),float(xyz.y)))
    else:
        raise ValueError('Nesting por contorno aceita apenas CIRCLE e POLYLINE/LWPOLYLINE fechada reta.')
    if len(pts)<3: raise ValueError('Contorno requer ao menos três vértices.')
    poly=Polygon(pts)
    if not poly.is_valid or poly.is_empty or poly.area < EPS:
        raise ValueError('Polilinha auto-intersectante, degenerada ou inválida.')
    return poly


def _validate_nest(w,h,margin,spacing,copies):
    if not all(math.isfinite(v) for v in (w,h,margin,spacing)) or w<=0 or h<=0 or margin<0 or spacing<0:
        raise ValueError('Chapa positiva, margem e espaçamento não negativos.')
    if not isinstance(copies,int) or copies<1 or copies>15:
        raise ValueError('Cópias por peça: 1 a 15.')
    if margin*2>=min(w,h):raise ValueError('Margem maior que a área útil da chapa.')


def _normalize(shape):
    x0,y0,x1,y1=shape.bounds
    return translate(shape,-x0,-y0), x1-x0, y1-y0


def _candidates(occupied, shape_w, shape_h, usable, spacing, max_scan=2600):
    """Cantos de peças existentes + grade pequena determinística (heurística).
    Não garante aproveitamento global ótimo.
    """
    minx,miny,maxx,maxy=usable.bounds
    xs={minx};ys={miny}
    for occ in occupied:
        a,b,c,d=occ.bounds
        for x in (a, c+spacing, c-shape_w, a-shape_w-spacing):
            if minx-EPS<=x and x+shape_w<=maxx+EPS: xs.add(max(minx,x))
        for y in (b, d+spacing, d-shape_h, b-shape_h-spacing):
            if miny-EPS<=y and y+shape_h<=maxy+EPS:ys.add(max(miny,y))
    # A grade complementa candidatos para contornos côncavos.
    free_w=maxx-minx-shape_w;free_h=maxy-miny-shape_h
    intervals=24
    if free_w>EPS:
        xs.update(minx+i*free_w/intervals for i in range(intervals+1))
    if free_h>EPS:
        ys.update(miny+i*free_h/intervals for i in range(intervals+1))
    # Prioriza encaixes compactos na direção vertical.
    positions=sorted(((round(x,7),round(y,7)) for x in xs for y in ys), key=lambda p:(p[1],p[0]))
    return positions[:max_scan]


def true_shape_nesting(path,sheet_w,sheet_h,spacing=2.0,margin=2.0,copies=1,rotations=(0,90,180,270)):
    """Nesting heurístico de contornos 2D planos fechados em UMA chapa.

    Saída conserva círculos como CIRCLE e polilinhas como suas entidades originais;
    valida geometria antes de colocar. Limite de 60 contornos e sem buracos
    associados por hierarquia; não é otimizador exato de corte.
    """
    _validate_nest(sheet_w,sheet_h,margin,spacing,copies)
    rots=tuple(int(r) for r in rotations)
    if not rots or any(r not in (0,90,180,270) for r in rots):
        raise ValueError('Rotações permitidas: 0, 90, 180 e 270 graus.')
    doc=_load(path);msp=doc.modelspace();original=list(msp)
    if int(doc.header.get('$INSUNITS',0)) not in (0,4):
        raise ValueError('DXF não está em milímetros; corrija a unidade na origem.')
    if not original:raise ValueError('DXF vazio.')
    if len(original)*copies>MAX_PIECES:raise ValueError(f'Máximo de {MAX_PIECES} peças por operação.')
    pieces=[]
    for e in original:
        try:poly=_to_polygon(e)
        except ValueError as ex:raise ValueError(f'Entidade {e.dxftype()} ({e.dxf.handle}): {ex}') from ex
        pieces.extend((e,poly,i) for i in range(copies))
    pieces.sort(key=lambda item:(-item[1].area,-max(item[1].bounds[2]-item[1].bounds[0],item[1].bounds[3]-item[1].bounds[1])))
    usable=box(margin,margin,sheet_w-margin,sheet_h-margin)
    occupied=[];placed=[]
    for idx,(ent,poly,copy_index) in enumerate(pieces):
        chosen=None
        for deg in rots:
            norm,ww,hh=_normalize(rotate(poly,deg,origin=(0,0)))
            if ww>sheet_w-2*margin+EPS or hh>sheet_h-2*margin+EPS: continue
            for x,y in _candidates(occupied,ww,hh,usable,spacing):
                candidate=translate(norm,x,y)
                if not usable.buffer(EPS).covers(candidate):continue
                if any(candidate.distance(other)<spacing-EPS if spacing>EPS else
                       candidate.intersection(other).area>EPS for other in occupied):continue
                chosen=(ent,poly,candidate,deg,x,y,copy_index)
                break
            if chosen:break
        if not chosen:
            raise ValueError('Não couberam todas as peças em UMA chapa: falhou na peça '
                             f'{idx+1} de {len(pieces)}. Tente outra rotação/chapa ou reduza o espaçamento.')
        occupied.append(chosen[2]);placed.append(chosen)
    transformed=[]
    for e,oldpoly,finalpoly,deg,x,y,copy_index in placed:
        clone=e.copy()
        try:
            if deg: clone.transform(Matrix44.z_rotate(math.radians(deg)))
            geometry_rotated=rotate(oldpoly,deg,origin=(0,0))
            poly_minx,poly_miny,_,_=geometry_rotated.bounds
            clone.transform(Matrix44.translate(x-poly_minx,y-poly_miny,0))
        except Exception as exc:raise ValueError(f'Erro ao transformar peça {e.dxf.handle}: {exc}') from exc
        transformed.append(clone)
    for e in original:msp.delete_entity(e)
    for e in transformed:msp.add_entity(e)
    # Definir unidades em mm apenas se já declaradas em mm ou não declaradas.
    insunits=int(doc.header.get('$INSUNITS',0))
    if insunits not in (0,4):raise ValueError(f'DXF não está em milímetros ($INSUNITS={insunits}).')
    doc.header['$INSUNITS']=4
    output=safe_output(path,'_nest_contorno_v5')
    doc.saveas(output)
    utilization=sum(p.area for _,p,_ in pieces)/(sheet_w*sheet_h)*100
    return TrueNestResult(output,len(placed),round(utilization,3),sheet_w,sheet_h,
        'Heurística, sem garantia de mínimo desperdício; contornos independentes, sem hierarquia de furos.')


def offset_only(path,distance):
    """Exporta SOMENTE a camada nova de offset, sem duplicar os originais ao importar no CDR."""
    from laser_core import create_offsets
    result,num,skipped=create_offsets(path,distance)
    doc=ezdxf.readfile(result)
    msp=doc.modelspace()
    for ent in list(msp):
        if ent.dxf.get('layer','0')!='LASER_OFFSET':msp.delete_entity(ent)
    doc.header['$INSUNITS']=4
    output=safe_output(path,'_offset_apenas_v5')
    doc.saveas(output)
    return output,num,skipped


def rdworks_clean_export(path):
    """Regrava DXF na versão do arquivo-fonte, valida tipos e unidades.

    Não gera arquivo .rd do controlador. Importação no RDWorks deve ser validada.
    """
    doc=_load(path)
    existing=int(doc.header.get('$INSUNITS',0))
    if existing not in (0,4):raise ValueError('DXF de entrada não está em milímetros. Corrija a unidade na origem.')
    supported={'LINE','LWPOLYLINE','POLYLINE','CIRCLE','ARC'}
    msp=doc.modelspace(); entities=list(msp)
    if not entities:raise ValueError('Arquivo DXF vazio.')
    errors=[]
    for e in entities:
        if e.dxftype() not in supported: errors.append(e.dxftype())
        if e.dxftype() in ('LWPOLYLINE','POLYLINE','LINE','CIRCLE','ARC') and not _flat_xy(e):
            errors.append(e.dxftype()+' 3D')
    if errors:raise ValueError('Entidades não garantidas para exportação segura: '+', '.join(sorted(set(errors))))
    doc.header['$INSUNITS']=4
    doc.header['$MEASUREMENT']=1
    target=safe_output(path,'_RDWorks_mm_v5')
    doc.saveas(target)
    check=ezdxf.readfile(target)
    if len(check.modelspace())!=len(entities):raise ValueError('Falha na revalidação do DXF gerado.')
    return target,len(entities)
