"""Núcleo independente do Laser Tools Free v3 (DXF). Sem código do eCut.

Decisões de segurança: operações trabalham em memória e gravam outro arquivo;
camadas/aparência fazem parte da identidade; entidades complexas não são
simplificadas silenciosamente. Medidas são geométricas, não são simulação CAM.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import ezdxf
from ezdxf import bbox
from ezdxf.math import Matrix44

EPS = 1e-8


def safe_output(source, suffix):
    source = Path(source)
    output = source.with_name(source.stem + suffix + source.suffix)
    i = 2
    while output.exists():
        output = source.with_name(f"{source.stem}{suffix}_{i}{source.suffix}")
        i += 1
    return output


def _load(path):
    path = Path(path)
    if not path.is_file() or path.suffix.lower() != '.dxf':
        raise ValueError('Selecione um DXF existente.')
    return ezdxf.readfile(str(path))


def _save(doc, source, suffix):
    output = safe_output(source, suffix)
    doc.saveas(str(output))
    return output


def _round(p, precision):
    return tuple(round(float(v), precision) for v in p)


def _style(e):
    """Aparência e função de corte: nunca fundir entidades de camadas diferentes."""
    return (e.dxf.get('layer', '0'), e.dxf.get('color', 256),
            e.dxf.get('true_color', None), e.dxf.get('linetype', 'BYLAYER'),
            e.dxf.get('lineweight', -1), e.dxf.get('transparency', None),
            e.dxf.get('invisible', 0), e.dxf.get('extrusion', (0, 0, 1)))


def _flat_xy(e):
    normal = e.dxf.get('extrusion', (0, 0, 1))
    return abs(float(normal[0])) < EPS and abs(float(normal[1])) < EPS and abs(float(normal[2])-1) < EPS


def _line_key(e, precision):
    a = _round(e.dxf.start, precision)
    b = _round(e.dxf.end, precision)
    return (_style(e), min(a, b), max(a, b))


def _poly_info(e):
    """Retorna vértices (x,y,z,bulge) e flag fechamento de LW ou POLYLINE 2D."""
    if e.dxftype() == 'LWPOLYLINE':
        z = float(e.dxf.get('elevation', 0))
        pts = [(float(x), float(y), z, float(b)) for x,y,_,_,b in e.get_points('xyseb')]
        return pts, bool(e.closed)
    if e.dxftype() == 'POLYLINE' and e.is_2d_polyline:
        pts = [(*map(float, v.dxf.location), float(v.dxf.get('bulge',0))) for v in e.vertices]
        return pts, bool(e.is_closed)
    return None


def _poly_key(e, precision):
    info = _poly_info(e)
    if not info or not _flat_xy(e):
        return None
    pts, closed = info
    if not pts:
        return None
    # Com arcos (bulge), só normalizar a rotação da origem de polilinhas
    # fechadas: inverter a ordem exige inverter sinais e índices dos bulges.
    rounded = tuple(_round(p, precision) for p in pts)
    candidates = []
    for seq in (rounded[i:] + rounded[:i] for i in range(len(rounded))) if closed else (rounded,):
        candidates.append(seq)
    # Inversão apenas de polilinhas sem bulge e sem largura variável.
    has_width = (e.has_width if e.dxftype() == 'LWPOLYLINE' else any(
        v.dxf.get('start_width',0) or v.dxf.get('end_width',0) for v in e.vertices))
    has_bulge = any(abs(p[3]) > 10**(-precision) for p in pts)
    if not has_bulge and not has_width:
        rev = tuple(reversed(rounded))
        for seq in (rev[i:] + rev[:i] for i in range(len(rev))) if closed else (rev,):
            candidates.append(seq)
    widths = ()
    if e.dxftype() == 'LWPOLYLINE':
        widths = (round(float(e.dxf.get('const_width', 0)), precision),
                  tuple((round(float(p[2]),precision), round(float(p[3]),precision))
                        for p in e.get_points('xyseb')))
    else:
        widths = tuple((round(float(v.dxf.get('start_width',0)),precision),
                        round(float(v.dxf.get('end_width',0)),precision)) for v in e.vertices)
    # Não comparar LW com old POLYLINE; DXF semanticamente diferentes.
    return (e.dxftype(), _style(e), closed, widths, min(candidates))


def _straight_poly_segments(e):
    info = _poly_info(e)
    if not info or not _flat_xy(e):
        return []
    pts, closed = info
    if e.dxftype() == 'LWPOLYLINE' and e.has_width:
        return []
    if e.dxftype() == 'POLYLINE' and any(v.dxf.get('start_width',0) or v.dxf.get('end_width',0) for v in e.vertices):
        return []
    segments = []
    for i in range(len(pts) if closed else len(pts)-1):
        p = pts[i]; q = pts[(i+1) % len(pts)]
        if abs(p[3]) < EPS:
            segments.append((p[:3], q[:3]))
    return segments


def _subcovered(line_a, line_b, covers, tolerance):
    """Subtrai intervalos colineares cobertos, retornando fragmentos t em [0,1]."""
    ax,ay,az = map(float,line_a); bx,by,bz = map(float,line_b)
    vx,vy = bx-ax,by-ay
    length2 = vx*vx+vy*vy
    if length2 <= tolerance*tolerance:
        return [(0.,1.)]
    length = math.sqrt(length2)
    occupied=[]
    for p,q in covers:
        px,py,pz=map(float,p); qx,qy,qz=map(float,q)
        if abs(pz-az)>tolerance or abs(qz-bz)>tolerance:
            continue
        # teste perpendicular em unidades lineares
        if abs(vx*(py-ay)-vy*(px-ax))/length>tolerance: continue
        if abs(vx*(qy-ay)-vy*(qx-ax))/length>tolerance: continue
        t0=((px-ax)*vx+(py-ay)*vy)/length2
        t1=((qx-ax)*vx+(qy-ay)*vy)/length2
        lo,hi=max(0.,min(t0,t1)),min(1.,max(t0,t1))
        if hi-lo > tolerance/length:
            occupied.append((lo,hi))
    if not occupied:
        return [(0.,1.)]
    occupied.sort()
    fragments=[]; start=0.
    for lo,hi in occupied:
        if lo > start+tolerance/length:
            fragments.append((start,lo))
        start=max(start,hi)
    if start < 1.-tolerance/length:
        fragments.append((start,1.))
    return fragments


@dataclass
class CleanResult:
    output: Path
    lines_removed: int
    polylines_removed: int
    lines_split: int
    line_fragments_created: int
    notes: str


def clean_duplicates(path, precision=4, partial=True):
    if not 2 <= precision <= 7:
        raise ValueError('Precisão entre 2 e 7 casas decimais.')
    doc=_load(path); msp=doc.modelspace()
    lines_seen=set(); poly_seen=set()
    removed_lines=removed_polys=split_lines=fragments=0
    for e in list(msp):
        if e.dxftype() == 'LWPOLYLINE' or (e.dxftype() == 'POLYLINE' and e.is_2d_polyline):
            k=_poly_key(e, precision)
            if k is None: continue
            if k in poly_seen:
                msp.delete_entity(e); removed_polys+=1
            else:
                poly_seen.add(k)
    covers=defaultdict(list)
    if partial:
        for e in msp:
            if e.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
                covers[_style(e)].extend(_straight_poly_segments(e))
    for e in list(msp):
        if e.dxftype()!='LINE': continue
        a=tuple(map(float,e.dxf.start)); b=tuple(map(float,e.dxf.end))
        if not partial:
            k=_line_key(e,precision)
            if k in lines_seen:
                msp.delete_entity(e); removed_lines+=1
            else:
                lines_seen.add(k)
            continue
        if math.dist(a,b)<=10**(-precision):
            # Não apagar intencionalmente geometria degenerada: apenas relatar.
            continue
        st=_style(e)
        sections=_subcovered(a,b,covers[st],10**(-precision))
        if len(sections)==1 and abs(sections[0][0])<EPS and abs(sections[0][1]-1)<EPS:
            covers[st].append((a,b)); continue
        if not sections:
            msp.delete_entity(e); removed_lines+=1; continue
        # Reusar a primeira linha original, preservando propriedades e XDATA.
        def coords(t): return tuple(a[i]+(b[i]-a[i])*t for i in range(3))
        e.dxf.start=coords(sections[0][0]);e.dxf.end=coords(sections[0][1])
        for lo,hi in sections[1:]:
            other=e.copy(); other.dxf.start=coords(lo); other.dxf.end=coords(hi)
            msp.add_entity(other); fragments+=1
        split_lines+=1
        for lo,hi in sections: covers[st].append((coords(lo),coords(hi)))
    output=_save(doc,path,'_limpo_v3')
    return CleanResult(output, removed_lines, removed_polys, split_lines, fragments,
        'Sobreposições em arcos, splines ou entre polilinhas distintas não são modificadas.')


def _length_area(e):
    """Retorna comprimento, área geométrica nominal (sem desconto de furos), motivo."""
    kind=e.dxftype()
    if kind=='LINE':
        return math.dist(e.dxf.start,e.dxf.end),0.,''
    if kind=='CIRCLE':
        r=float(e.dxf.radius)
        return 2*math.pi*r, math.pi*r*r, ''
    if kind=='ARC':
        ang=math.radians((float(e.dxf.end_angle)-float(e.dxf.start_angle))%360)
        return float(e.dxf.radius)*ang,0.,''
    info=_poly_info(e)
    if info:
        if not _flat_xy(e): return 0.,0.,'extrusão não plana'
        pts,closed=info
        if len(pts)<2: return 0.,0.,'poucos vértices'
        length=area_cross=area_arc=0.
        for i in range(len(pts) if closed else len(pts)-1):
            x,y,z,bulge=pts[i]; X,Y,Z,_=pts[(i+1)%len(pts)]
            if abs(z-Z)>EPS: return 0.,0.,'polilinha 3D'
            chord=math.hypot(X-x,Y-y)
            theta=4*math.atan(bulge) if abs(bulge)>EPS else 0.
            if abs(theta)>EPS and chord>EPS:
                radius=abs(chord/(2*math.sin(theta/2)))
                length+=abs(radius*theta)
                area_arc+=radius*radius*(theta-math.sin(theta))/2
            else: length+=chord
            area_cross+=(x*Y-X*y)/2
        return length,abs(area_cross+area_arc) if closed else 0.,''
    return 0.,0.,'tipo não medido'


def report(path, unit='mm', material_per_m2=0., cut_per_m=0., setup=0.):
    doc=_load(path);msp=doc.modelspace()
    counts=Counter(e.dxftype() for e in msp)
    ext=bbox.extents(msp, fast=True)
    width=ext.extmax.x-ext.extmin.x if ext.has_data else 0.
    height=ext.extmax.y-ext.extmin.y if ext.has_data else 0.
    length=area=0.;skipped=Counter()
    for e in msp:
        l,a,msg=_length_area(e)
        length+=l;area+=a
        if msg:skipped[f'{e.dxftype()}: {msg}']+=1
    unit_map={'mm':1.,'cm':10.,'m':1000.}
    if unit not in unit_map:raise ValueError('Unidade deve ser mm, cm ou m.')
    mm=unit_map[unit]
    for number in [material_per_m2,cut_per_m,setup]:
        if not math.isfinite(number) or number<0:raise ValueError('Preços devem ser positivos e finitos.')
    area_m2=area*(mm/1000)**2;length_m=length*mm/1000
    return dict(types=dict(counts), width=width, height=height, unit=unit,
                insunits=doc.header.get('$INSUNITS',0), length=length,
                area=area, length_m=length_m, area_m2=area_m2,
                material_cost=area_m2*material_per_m2,
                cut_cost=length_m*cut_per_m,
                total=area_m2*material_per_m2+length_m*cut_per_m+setup,
                setup=setup, skipped=dict(skipped), entities=sum(counts.values()),
                warnings='Áreas fechadas são somadas sem descontar furos nem sobreposições. Não é estimativa de tempo da máquina.')


def scale_and_copy(path,sx=100.,sy=100.,copies=1,gap_x=5.,gap_y=0.):
    if not all(map(math.isfinite,[sx,sy,gap_x,gap_y])) or sx<=0 or sy<=0 or not 1<=copies<=100 or gap_x<0:
        raise ValueError('Escalas devem ser positivas; cópias entre 1 e 100; espaçamento X não negativo.')
    doc=_load(path);msp=doc.modelspace()
    items=list(msp)
    if not items:raise ValueError('DXF vazio.')
    # Primeiro testar em clones para que qualquer transformação impossível pare o processo.
    matrix=Matrix44.scale(sx/100,sy/100,1)
    clones=[]
    for e in items:
        c=e.copy()
        try:c.transform(matrix)
        except Exception as exc:raise ValueError(f'Não foi possível escalar {e.dxftype()} ({e.dxf.handle}): {exc}') from exc
        clones.append(c)
    for e in items:e.transform(matrix)
    ext=bbox.extents(items,fast=True)
    if not ext.has_data:raise ValueError('Não foi possível medir o desenho.')
    w=ext.extmax.x-ext.extmin.x
    for i in range(1,copies):
        dx=i*(w+gap_x);dy=i*gap_y
        for e in items:
            c=e.copy()
            try:c.transform(Matrix44.translate(dx,dy,0))
            except Exception as exc:raise ValueError(f'Falha ao multiplicar {e.dxftype()}: {exc}') from exc
            msp.add_entity(c)
    return _save(doc,path,'_escala_v3')


def _nest_eligible(e):
    if not _flat_xy(e):return False
    if e.dxftype()=='CIRCLE':return True
    if e.dxftype()=='LWPOLYLINE':return bool(e.closed)
    if e.dxftype()=='POLYLINE':return bool(e.is_2d_polyline and e.is_closed)
    return False


def rectangular_nesting(path,sheet_w,sheet_h,spacing=2.,margin=2.,copies=1,allow_rotate=True):
    """Encaixe retangular conservador, NÃO nesting por forma real."""
    values=(sheet_w,sheet_h,spacing,margin)
    if not all(math.isfinite(v) for v in values) or sheet_w<=0 or sheet_h<=0 or spacing<0 or margin<0:
        raise ValueError('Chapa positiva; espaçamento e margem não negativos.')
    if not isinstance(copies,int) or not 1<=copies<=100:raise ValueError('Use 1 a 100 cópias por contorno.')
    doc=_load(path);msp=doc.modelspace();original=list(msp)
    if not original:raise ValueError('DXF vazio.')
    invalid=[f'{e.dxftype()} ({e.dxf.handle})' for e in original if not _nest_eligible(e)]
    if invalid:
        raise ValueError('Nesting seguro aceita somente contornos fechados LWPOLYLINE, POLYLINE 2D e CIRCLE. Não processado: '+', '.join(invalid[:8]))
    shapes=[]
    for e in original:
        ex=bbox.extents([e],fast=True)
        if not ex.has_data:raise ValueError(f'Não foi possível medir {e.dxf.handle}.')
        w=ex.extmax.x-ex.extmin.x;h=ex.extmax.y-ex.extmin.y
        if w<=EPS or h<=EPS:raise ValueError('Existe contorno com dimensão nula.')
        for i in range(copies):shapes.append((e,w,h,i))
    shapes.sort(key=lambda v: (-(v[1]*v[2]),-max(v[1],v[2])))
    right=sheet_w-margin;top=sheet_h-margin
    shelves=[];placements=[]
    for e,w,h,index in shapes:
        choices=[]
        orientations=[(w,h,False)]
        if allow_rotate and abs(w-h)>EPS:orientations.append((h,w,True))
        for sidx,s in enumerate(shelves):
            for ww,hh,rot in orientations:
                if hh<=s['height']+EPS and s['x']+ww<=right+EPS:
                    choices.append((0, right-(s['x']+ww),sidx,s['x'],s['y'],ww,hh,rot))
        y = margin if not shelves else shelves[-1]['y']+shelves[-1]['height']+spacing
        for ww,hh,rot in orientations:
            if margin+ww<=right+EPS and y+hh<=top+EPS:
                choices.append((1,top-(y+hh),len(shelves),margin,y,ww,hh,rot))
        if not choices:
            raise ValueError('Nem todas as peças cabem em UMA chapa. Reduza cópias/espaços ou amplie a chapa.')
        _,_,si,x,y,ww,hh,rot=min(choices,key=lambda c:(c[0],c[1],c[2]))
        if si==len(shelves):shelves.append({'x':margin,'y':y,'height':hh})
        shelves[si]['x']=x+ww+spacing
        placements.append((e,index,x,y,rot))
    # Gerar primeiro TODAS as transformações em cópias; se falhar não salvar.
    transformed=[]
    for e,index,x,y,rot in placements:
        c=e.copy()
        try:
            if rot:c.transform(Matrix44.z_rotate(math.pi/2))
            ex=bbox.extents([c],fast=True)
            c.transform(Matrix44.translate(x-ex.extmin.x,y-ex.extmin.y,0))
        except Exception as exc:raise ValueError(f'Falha ao encaixar {e.dxftype()}: {exc}') from exc
        transformed.append(c)
    for e in original:msp.delete_entity(e)
    for e in transformed:msp.add_entity(e)
    output=_save(doc,path,'_nest_retangular_v3')
    return output,len(transformed),len(shelves)


def create_offsets(path,distance):
    """Offset apenas de LW polylines fechadas RETAS e círculos (Shapely)."""
    if not math.isfinite(distance) or abs(distance)<EPS:raise ValueError('Distância deve ser diferente de zero.')
    try:from shapely.geometry import Polygon
    except ImportError as exc:raise RuntimeError('Instale o Shapely: py -m pip install shapely') from exc
    doc=_load(path);msp=doc.modelspace()
    layer='LASER_OFFSET'
    if layer not in doc.layers:doc.layers.new(layer, dxfattribs={'color': 1})
    outlines=[];skipped=Counter()
    for e in list(msp):
        if e.dxftype()=='CIRCLE' and _flat_xy(e):
            nr=e.dxf.radius+distance
            if nr>EPS:
                outlines.append(('circle',e,(tuple(e.dxf.center),nr)))
            else: skipped['círculo desapareceria']+=1
            continue
        if e.dxftype()!='LWPOLYLINE' or not e.closed or e.has_arc or e.has_width or not _flat_xy(e):
            skipped[e.dxftype()]+=1;continue
        pts=[(x,y) for x,y in e.get_points('xy')]
        if len(pts)<3:skipped['polilinha com poucos pontos']+=1;continue
        poly=Polygon(pts)
        if not poly.is_valid or poly.is_empty or poly.area<=EPS:
            skipped['polilinha inválida']+=1;continue
        result=poly.buffer(distance,join_style='mitre')
        if result.is_empty:skipped['offset vazio']+=1;continue
        shapes=[result] if result.geom_type=='Polygon' else list(result.geoms) if result.geom_type=='MultiPolygon' else []
        for shape in shapes:
            outlines.append(('poly',e,list(shape.exterior.coords)[:-1]))
            # Anéis internos devem ser gerados separadamente para não perdê-los.
            for ring in shape.interiors:outlines.append(('poly',e,list(ring.coords)[:-1]))
    if not outlines:raise ValueError('Não há contornos elegíveis. Use polilinhas fechadas retas ou círculos.')
    for kind,original,data in outlines:
        attrs={'layer':layer,'color':1}
        if kind=='circle':
            center,radius=data
            msp.add_circle(center,radius,dxfattribs=attrs)
        else:
            msp.add_lwpolyline(data,close=True,dxfattribs=attrs)
    return _save(doc,path,'_offset_v3'),len(outlines),dict(skipped)


def optimize_lines(path):
    """Apenas LINE, respeita camada; guloso e reversão para reduzir trajetos em vazio.

    Não garante que RDWorks respeite a sequência DXF; deve-se simular nele.
    """
    doc=_load(path);msp=doc.modelspace();items=list(msp)
    if not items:raise ValueError('DXF vazio.')
    if any(e.dxftype()!='LINE' for e in items):
        raise ValueError('Otimização v3 requer um DXF contendo somente LINE. Outros tipos não foram alterados.')
    groups=defaultdict(list)
    for e in items:groups[e.dxf.get('layer','0')].append(e)
    new_order=[];baseline=optimized=0.
    for layer,group in groups.items():
        # Parte sempre do início da primeira linha e preserva agrupamento por camada.
        remaining=list(group);first=remaining.pop(0);ordered=[(first,False)]
        end=tuple(first.dxf.end)
        while remaining:
            j,reverse=min(((j,rev) for j in range(len(remaining)) for rev in (False,True)),
                          key=lambda t: math.dist(end, remaining[t[0]].dxf.end if t[1] else remaining[t[0]].dxf.start))
            e=remaining.pop(j)
            optimized+=math.dist(end,e.dxf.end if reverse else e.dxf.start)
            end=tuple(e.dxf.start if reverse else e.dxf.end)
            ordered.append((e,reverse))
        for a,b in zip(group,group[1:]):baseline+=math.dist(a.dxf.end,b.dxf.start)
        new_order+=ordered
    for e,reverse in new_order:
        if reverse:e.dxf.start,e.dxf.end=e.dxf.end,e.dxf.start
        msp.unlink_entity(e)
        msp.add_entity(e)
    return _save(doc,path,'_percursos_v3'),baseline,optimized
