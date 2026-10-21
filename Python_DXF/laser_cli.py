"""Ponte de comandos sem interface gráfica. JSON na saída, erros via stderr/código 1."""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path
import ezdxf

from laser_core import clean_duplicates, rectangular_nesting, report, safe_output
from laser_advanced import true_shape_nesting, offset_only, rdworks_clean_export


def run(args):
    source=Path(args.input).resolve()
    if not source.is_file() or source.suffix.lower()!='.dxf':raise ValueError('Arquivo DXF de origem não encontrado.')
    # Transformar apenas unidades nativas em mm ou desenho sem unidade (Corel pode omitir $INSUNITS).
    doc=ezdxf.readfile(source)
    unit=int(doc.header.get('$INSUNITS',0))
    if unit not in (0,4):raise ValueError('Arquivo não está em milímetros ($INSUNITS='+str(unit)+').')
    if args.command=='clean':
        result=clean_duplicates(source,precision=4,partial=True)
        return {'output':str(result.output),'summary':f'{result.lines_removed} linhas e {result.polylines_removed} polilinhas duplicadas removidas; {result.lines_split} linhas divididas.'}
    if args.command=='rectangle':
        output,count,shelves=rectangular_nesting(source,args.width,args.height,args.spacing,args.margin, args.copies)
        return {'output':str(output),'summary':f'{count} peças em {shelves} faixas (caixas envolventes).'}
    if args.command=='shape':
        result=true_shape_nesting(source,args.width,args.height,args.spacing,args.margin,args.copies)
        return {'output':str(result.output),'summary':f'{result.piece_count} peças. Taxa geométrica de uso: {result.utilization_percent:.1f}%.'}
    if args.command=='offset':
        output,count,skipped=offset_only(source,args.distance)
        return {'output':str(output),'summary':f'{count} contornos gerados. Ignorados: {sum(skipped.values())}.'}
    if args.command=='report':
        data=report(source,unit='mm',material_per_m2=args.material,cut_per_m=args.cut,setup=args.setup)
        return {'output':'','summary':(f"Contagem: {data['entities']}; comprimento: {data['length_m']:.3f} m; "
                                    f"área somada: {data['area_m2']:.5f} m²; custo estimado R$ {data['total']:.2f}. "
                                    f"{data['warnings']}")}
    if args.command=='rdworks':
        output,count=rdworks_clean_export(source)
        return {'output':str(output),'summary':f'{count} entidades em DXF mm. Abrir e simular no RDWorks antes de cortar.'}
    raise ValueError('Operação não identificada.')


def build_parser():
    p=argparse.ArgumentParser(description='Laser Tools Free - motor DXF sem interface')
    p.add_argument('command',choices=['clean','rectangle','shape','offset','report','rdworks'])
    p.add_argument('input')
    p.add_argument('--width',type=float,default=300)
    p.add_argument('--height',type=float,default=200)
    p.add_argument('--spacing',type=float,default=2)
    p.add_argument('--margin',type=float,default=2)
    p.add_argument('--copies',type=int,default=1)
    p.add_argument('--distance',type=float,default=1)
    p.add_argument('--material',type=float,default=0)
    p.add_argument('--cut',type=float,default=0)
    p.add_argument('--setup',type=float,default=0)
    return p


if __name__=='__main__':
    # JSON contract: UTF-8 independent of the Windows ANSI codepage. The C#
    # plugin and tests explicitly decode UTF-8, even with Portuguese accents.
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='strict')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    try:
        args=build_parser().parse_args()
        answer=run(args)
        sys.stdout.write(json.dumps({'ok':True,**answer},ensure_ascii=False)+'\n')
    except Exception as ex:
        sys.stderr.write(str(ex)+'\n')
        sys.exit(1)
