from pathlib import Path
import json
import subprocess
import sys

import ezdxf
import pytest
from shapely.geometry import Polygon

from laser_advanced import true_shape_nesting, _to_polygon, offset_only, rdworks_clean_export


def make_dxf(tmp_path, name='pieces'):
    path=tmp_path/(name+'.dxf')
    d=ezdxf.new('R2000');d.header['$INSUNITS']=4
    m=d.modelspace()
    m.add_lwpolyline([(0,0),(20,0),(20,10),(0,10)],close=True)
    m.add_lwpolyline([(30,0),(40,0),(40,20),(30,20)],close=True)
    d.saveas(path)
    return path


def test_true_shape_nesting_original_intact(tmp_path):
    src=make_dxf(tmp_path)
    before=src.read_bytes()
    answer=true_shape_nesting(src,80,50,spacing=2,margin=2,copies=2)
    assert src.read_bytes()==before
    assert answer.output!=src and answer.output.is_file()
    result=ezdxf.readfile(answer.output)
    assert result.header['$INSUNITS']==4
    assert len(result.modelspace())==4
    pieces=[_to_polygon(e) for e in result.modelspace()]
    for i,a in enumerate(pieces):
        x0,y0,x1,y1=a.bounds
        assert x0 >= 2-1e-5 and y0>=2-1e-5 and x1<=78+1e-5 and y1<=48+1e-5
        for b in pieces[i+1:]:assert a.distance(b)>=2-1e-5


def test_true_shape_nesting_rejects_unsafe_open_geometry(tmp_path):
    src=tmp_path/'unsafe.dxf'
    d=ezdxf.new('R2000');d.header['$INSUNITS']=4;d.modelspace().add_line((0,0),(20,20));d.saveas(src)
    with pytest.raises(ValueError,match='Entidade'):true_shape_nesting(src,80,50)
    assert len(list(tmp_path.glob('*nest_contorno*')))==0


def test_true_shape_nesting_rejects_wrong_units(tmp_path):
    src=make_dxf(tmp_path)
    d=ezdxf.readfile(src);d.header['$INSUNITS']=1;d.saveas(src)
    with pytest.raises(ValueError,match='milímetros'):true_shape_nesting(src,80,50)


def test_true_shape_nesting_failure_leaves_source_unchanged(tmp_path):
    src=make_dxf(tmp_path);before=src.read_bytes()
    with pytest.raises(ValueError,match='couberam'):true_shape_nesting(src,22,11,margin=1)
    assert src.read_bytes()==before
    assert not list(tmp_path.glob('*nest_contorno*'))


def test_true_shape_nesting_circles_preserved(tmp_path):
    src=tmp_path/'circles.dxf';d=ezdxf.new('R2000');d.header['$INSUNITS']=4
    d.modelspace().add_circle((0,0),5);d.saveas(src)
    result=true_shape_nesting(src,40,30,spacing=0.5,margin=1,copies=3)
    other=ezdxf.readfile(result.output)
    assert [e.dxftype() for e in other.modelspace()]==['CIRCLE']*3


def test_true_shape_rejects_bulge(tmp_path):
    src=tmp_path/'bulge.dxf';d=ezdxf.new('R2000');d.header['$INSUNITS']=4
    d.modelspace().add_lwpolyline([(0,0,0,0,0.25),(10,0),(10,10),(0,10)],format='xyseb',close=True)
    d.saveas(src)
    with pytest.raises(ValueError,match='bulge'):true_shape_nesting(src,100,100)


def test_offset_only_does_not_duplicate_original(tmp_path):
    src=make_dxf(tmp_path)
    original=src.read_bytes()
    output,count,skipped=offset_only(src,1)
    ents=list(ezdxf.readfile(output).modelspace())
    assert count==2 and len(ents)==2
    assert all(e.dxf.layer=='LASER_OFFSET' for e in ents)
    assert src.read_bytes()==original


def test_rdworks_export_mm_and_rejects_unsupported(tmp_path):
    src=make_dxf(tmp_path)
    original=src.read_bytes()
    output,num=rdworks_clean_export(src)
    assert num==2 and ezdxf.readfile(output).header['$INSUNITS']==4
    assert src.read_bytes()==original
    src2=tmp_path/'text.dxf';d=ezdxf.new('R2000');d.header['$INSUNITS']=4;d.modelspace().add_text('olá');d.saveas(src2)
    with pytest.raises(ValueError,match='TEXT'):rdworks_clean_export(src2)


def test_cli_process_and_json(tmp_path):
    src=make_dxf(tmp_path)
    cli=Path(__file__).resolve().parents[1]/'laser_cli.py'
    run=subprocess.run([sys.executable,str(cli),'shape',str(src),'--width','100','--height','70'],capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    data=json.loads(run.stdout)
    assert data['ok'] is True and Path(data['output']).is_file()
    assert Path(data['output']).resolve()!=src.resolve()


def test_cli_error_nonzero_no_output(tmp_path):
    src=tmp_path/'x.dxf';d=ezdxf.new('R2000');d.header['$INSUNITS']=4;d.modelspace().add_line((0,0),(1,1));d.saveas(src)
    cli=Path(__file__).resolve().parents[1]/'laser_cli.py'
    run=subprocess.run([sys.executable,str(cli),'shape',str(src)],capture_output=True,text=True)
    assert run.returncode!=0 and 'Entidade' in run.stderr
    assert not list(tmp_path.glob('*nest_contorno*'))


def test_cli_report(tmp_path):
    src=make_dxf(tmp_path)
    cli=Path(__file__).resolve().parents[1]/'laser_cli.py'
    run=subprocess.run([sys.executable,str(cli),'report',str(src),'--cut','12.5'],capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    assert 'custo estimado' in json.loads(run.stdout)['summary']
