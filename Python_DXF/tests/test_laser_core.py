import math
from pathlib import Path
import pytest
import ezdxf

from laser_core import (clean_duplicates, report, scale_and_copy,
                        rectangular_nesting, create_offsets, optimize_lines)


def docfile(tmp_path, draw, name='entrada.dxf'):
    d=ezdxf.new('R2010');d.header['$INSUNITS']=4
    draw(d.modelspace())
    p=tmp_path/name;d.saveas(p)
    return p


def types(path):
    d=ezdxf.readfile(path)
    return d, list(d.modelspace())


def test_preserve_source_and_unique_names(tmp_path):
    p=docfile(tmp_path, lambda m: (m.add_line((0,0),(10,0)), m.add_line((10,0),(0,0))))
    before=p.read_bytes()
    r1=clean_duplicates(p)
    r2=clean_duplicates(p)
    assert p.read_bytes()==before
    assert r1.output!=r2.output
    assert r1.lines_removed==1
    assert len(types(r1.output)[1])==1


def test_lines_respect_layers(tmp_path):
    def draw(m):
        m.add_line((0,0),(10,0),dxfattribs={'layer':'CORTE'})
        m.add_line((10,0),(0,0),dxfattribs={'layer':'GRAVACAO'})
    p=docfile(tmp_path,draw)
    result=clean_duplicates(p)
    assert result.lines_removed==0
    assert len(types(result.output)[1])==2


def test_partial_overlap_line_and_long_line(tmp_path):
    def draw(m):
        m.add_line((0,0),(10,0))
        m.add_line((5,0),(15,0))
    p=docfile(tmp_path,draw)
    res=clean_duplicates(p,partial=True)
    assert res.lines_split==1
    _,entities=types(res.output)
    spans=sorted((round(e.dxf.start.x,4),round(e.dxf.end.x,4)) for e in entities)
    assert spans==[(0.,10.),(10.,15.)]


def test_middle_overlap_creates_two_fragments(tmp_path):
    p=docfile(tmp_path,lambda m:(m.add_line((4,0),(6,0)),m.add_line((0,0),(10,0))))
    r=clean_duplicates(p)
    assert r.line_fragments_created==1
    _,entities=types(r.output)
    assert len(entities)==3
    assert sorted(round(math.dist(e.dxf.start,e.dxf.end),4) for e in entities)==[2,4,4]


def test_polyline_full_duplicate_rotated_and_reversed(tmp_path):
    def draw(m):
        m.add_lwpolyline([(0,0),(10,0),(10,10),(0,10)],close=True)
        m.add_lwpolyline([(10,10),(0,10),(0,0),(10,0)],close=True)
        m.add_lwpolyline([(0,10),(10,10),(10,0),(0,0)],close=True)
    p=docfile(tmp_path,draw)
    r=clean_duplicates(p)
    assert r.polylines_removed==2
    assert len(types(r.output)[1])==1


def test_polyline_different_layers_kept(tmp_path):
    p=docfile(tmp_path,lambda m:(
        m.add_lwpolyline([(0,0),(10,0),(10,10)],close=True,dxfattribs={'layer':'A'}),
        m.add_lwpolyline([(0,0),(10,0),(10,10)],close=True,dxfattribs={'layer':'B'})))
    r=clean_duplicates(p)
    assert r.polylines_removed==0


def test_line_redundant_against_straight_polyline_edge(tmp_path):
    p=docfile(tmp_path,lambda m:(
        m.add_lwpolyline([(0,0),(10,0),(10,10)],close=True),
        m.add_line((2,0),(7,0))))
    r=clean_duplicates(p)
    assert r.lines_removed==1
    assert len(types(r.output)[1])==1


def test_arc_polyline_undisturbed(tmp_path):
    p=docfile(tmp_path,lambda m:m.add_lwpolyline([(0,0,1),(10,0,0),(10,10,0)],format='xyb',close=True))
    r=clean_duplicates(p)
    assert len(types(r.output)[1])==1


def test_report_area_perimeter_and_prices(tmp_path):
    p=docfile(tmp_path,lambda m:m.add_lwpolyline([(0,0),(100,0),(100,50),(0,50)],close=True))
    r=report(p,unit='mm',material_per_m2=100,cut_per_m=10,setup=2)
    assert r['length']==pytest.approx(300)
    assert r['area']==pytest.approx(5000)
    assert r['total']==pytest.approx(5.5)


def test_report_circle(tmp_path):
    p=docfile(tmp_path,lambda m:m.add_circle((0,0),10))
    r=report(p)
    assert r['length']==pytest.approx(20*math.pi)
    assert r['area']==pytest.approx(100*math.pi)


def test_report_bulge_semicircle(tmp_path):
    p=docfile(tmp_path,lambda m:m.add_lwpolyline([(0,0,1),(10,0,0)],format='xyb',close=True))
    r=report(p)
    assert r['length']==pytest.approx(5*math.pi+10)
    assert r['area']==pytest.approx(math.pi*25/2)


def test_scale_nonuniform_with_bulge_rejected_no_output(tmp_path):
    p=docfile(tmp_path,lambda m:m.add_lwpolyline([(0,0,1),(10,0,0)],format='xyb'))
    before=p.read_bytes()
    with pytest.raises(ValueError):scale_and_copy(p,200,100)
    assert p.read_bytes()==before
    assert len(list(tmp_path.glob('*_escala_v3.dxf')))==0


def test_scale_uniform_and_copies(tmp_path):
    p=docfile(tmp_path,lambda m:m.add_line((0,0),(10,0)))
    out=scale_and_copy(p,200,200,3,5)
    _,entities=types(out)
    assert len(entities)==3
    assert [round(e.dxf.start.x,3) for e in entities]==[0,25,50]


def test_rectangular_nesting_has_no_overlap_and_source_preserved(tmp_path):
    def draw(m):
        m.add_lwpolyline([(40,40),(60,40),(60,50),(40,50)],close=True)
        m.add_circle((30,30),5)
    p=docfile(tmp_path,draw)
    original=p.read_bytes()
    out,n,shelves=rectangular_nesting(p,100,100,spacing=2,margin=3,copies=2)
    assert n==4 and shelves>=1
    _,entities=types(out)
    assert len(entities)==4
    from ezdxf import bbox
    extents=[bbox.extents([e]) for e in entities]
    for b in extents:
        assert b.extmin.x>=3-1e-7 and b.extmin.y>=3-1e-7
        assert b.extmax.x<=97+1e-7 and b.extmax.y<=97+1e-7
    for i,a in enumerate(extents):
        for b in extents[i+1:]:
            width=min(a.extmax.x,b.extmax.x)-max(a.extmin.x,b.extmin.x)
            height=min(a.extmax.y,b.extmax.y)-max(a.extmin.y,b.extmin.y)
            assert width<=0 or height<=0
    assert p.read_bytes()==original


def test_nesting_rejects_open_line_no_output(tmp_path):
    p=docfile(tmp_path,lambda m:m.add_line((0,0),(10,0)))
    with pytest.raises(ValueError):rectangular_nesting(p,100,100)
    assert not list(tmp_path.glob('*nest*'))


def test_nesting_fails_if_not_fit(tmp_path):
    p=docfile(tmp_path,lambda m:m.add_lwpolyline([(0,0),(110,0),(110,10),(0,10)],close=True))
    with pytest.raises(ValueError):rectangular_nesting(p,100,100,margin=1)


def test_offset_adds_separate_layer(tmp_path):
    p=docfile(tmp_path,lambda m:m.add_lwpolyline([(0,0),(10,0),(10,10),(0,10)],close=True))
    out,n,skipped=create_offsets(p,2)
    assert n==1
    _,entities=types(out)
    assert len(entities)==2
    assert entities[1].dxf.layer=='LASER_OFFSET'
    assert report(out)['area']>100


def test_offset_circle_shrinking(tmp_path):
    p=docfile(tmp_path,lambda m:m.add_circle((0,0),10))
    out,n,_=create_offsets(p,-3)
    assert n==1
    _,entities=types(out)
    assert entities[1].dxf.radius==pytest.approx(7)


def test_optimize_only_line_and_preserves_geometry(tmp_path):
    def draw(m):
        m.add_line((0,0),(1,0))
        m.add_line((100,0),(101,0))
        m.add_line((2,0),(3,0))
    p=docfile(tmp_path,draw)
    out,base,optimized=optimize_lines(p)
    assert optimized<base
    _,entities=types(out)
    assert len(entities)==3
    assert sorted(round(min(e.dxf.start.x,e.dxf.end.x)) for e in entities)==[0,2,100]


def test_optimize_rejects_polylines(tmp_path):
    p=docfile(tmp_path,lambda m:m.add_lwpolyline([(0,0),(10,0)],close=False))
    with pytest.raises(ValueError):optimize_lines(p)


def test_old_polyline_2d_duplicate_and_nesting(tmp_path):
    def draw(m):
        m.add_polyline2d([(0,0),(20,0),(20,10),(0,10)],close=True)
        m.add_polyline2d([(20,10),(0,10),(0,0),(20,0)],close=True)
    p=docfile(tmp_path,draw)
    assert clean_duplicates(p).polylines_removed==1
    assert report(p)['area']==pytest.approx(400)
    out,qty,_=rectangular_nesting(p,200,100)
    assert qty==2
    assert len(types(out)[1])==2


def test_color_matters_for_line_cleanup(tmp_path):
    p=docfile(tmp_path,lambda m:(
        m.add_line((0,0),(10,0),dxfattribs={'color':1}),
        m.add_line((0,0),(10,0),dxfattribs={'color':2})))
    assert clean_duplicates(p).lines_removed==0


def test_open_polylines_not_offset(tmp_path):
    p=docfile(tmp_path,lambda m:m.add_lwpolyline([(0,0),(10,0),(10,10)],close=False))
    with pytest.raises(ValueError):create_offsets(p,2)
    assert len(list(tmp_path.glob('*_offset_v3.dxf')))==0
