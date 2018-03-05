# import matplotlib.pyplot as plt
# import numpy as np
# from matplotlib import collections  as mc
# from matplotlib import patches as mp

from gm_base.geometry_files.polygons import *
from gm_base.geometry_files.plot_polygons import *


class TestPoint:
    def test_insert_segment_0(self):
        decomp = PolygonDecomposition()
        # insert to free point
        pt0 = decomp._add_free_point([0.0, 0.0], decomp.outer_polygon)
        assert pt0.insert_segment(np.array([10, 1])) == None

    def test_insert_segment_1(self):
        decomp = PolygonDecomposition()
        # insert to single segment point
        pt1 = decomp._add_free_point([0.0, 0.0], decomp.outer_polygon)
        pt2 = decomp._add_free_point([1.0, 1.0], decomp.outer_polygon)
        sg1 = decomp.new_segment(pt1, pt2)
        assert sg1.is_dendrite()
        assert pt1.insert_segment(np.array([0, 1.0])) == ( (sg1, right_side), (sg1, left_side), sg1.wire[out_vtx])
        assert pt1.insert_segment(np.array([0, -1.0])) == ((sg1, right_side), (sg1, left_side), sg1.wire[out_vtx])

    def test_insert_segment_2(self):
        decomp = PolygonDecomposition()
        # insert to two segment point
        pt1 = decomp._add_free_point([0.0, 0.0], decomp.outer_polygon)
        pt2 = decomp._add_free_point([1.0, 1.0], decomp.outer_polygon)
        pt3 = decomp._add_free_point([-1.0, -0.1], decomp.outer_polygon)
        sg1 = decomp.new_segment(pt1, pt2)
        sg2 = decomp.new_segment(pt1, pt3)

        assert sg1.is_dendrite()
        assert sg2.is_dendrite()
        assert sg1.wire[out_vtx] == sg2.wire[out_vtx]

        assert pt1.insert_segment(np.array([0.0, 1.0])) == ((sg2, right_side), (sg1, left_side), sg1.wire[out_vtx])
        assert pt1.insert_segment(np.array([1.0, 0.01])) == ((sg1, right_side), (sg2, left_side), sg1.wire[out_vtx])
        assert pt1.insert_segment(np.array([-1.0, 0.001])) == ((sg2, right_side), (sg1, left_side), sg1.wire[out_vtx])

        # close polygon
        sg3 = decomp.new_segment(pt3, pt2)
        print(decomp)
        assert sg3.wire[right_side] == decomp.wires[1]
        assert sg3.wire[left_side] == decomp.wires[2]
        assert pt1.insert_segment(np.array([0.0, 1.0])) == ((sg2, right_side), (sg1, left_side), decomp.wires[1])
        assert pt1.insert_segment(np.array([1.0, 0.01])) == ((sg1, right_side), (sg2, left_side), decomp.wires[2])
        assert pt1.insert_segment(np.array([-1.0, 0.001])) == ((sg2, right_side), (sg1, left_side), decomp.wires[1])


class TestSegment:
    def test_is_on_x_line(self):
        sg = Segment(( Point([0.0, -0.001], None), Point([2.0, +0.001], None) ))
        assert sg.is_on_x_line([1.0 - 1e-4, 0.0])
        assert not sg.is_on_x_line([1.0, 0.0011])

        sg = Segment((Point([0.0, 1.0], None), Point([1.0, 0.0], None)))
        assert not sg.is_on_x_line([0.5 + 1e-1, 0.5 + 1e-1])

class TestWire:
    def test_contains(self):
        decomp = PolygonDecomposition()
        sg_a, = decomp.add_line((0,0), (2,0))
        sg_b, = decomp.add_line((2, 0), (2, 2))
        sg_c, = decomp.add_line((2, 2), (0, 2))
        sg_d, = decomp.add_line((0, 2), (0, 0))
        in_wire = sg_a.wire[left_side]
        assert in_wire.contains_point([-1, 1]) == False
        assert in_wire.contains_point([-0.0001, 1]) == False
        assert in_wire.contains_point([+0.0001, 1]) == True
        assert in_wire.contains_point([1.999, 1]) == True
        assert in_wire.contains_point([2.0001, 1]) == False
        # assert in_wire.contains_point([0, 1]) == True
        # assert in_wire.contains_point([2, 1]) == False

    def test_join_wires(self):
        decomp = PolygonDecomposition()
        sg, = decomp.add_line((0, 0), (0, 2))
        pt0 = sg.vtxs[0]
        decomp.add_line((0, 0), (2, 0))
        decomp.add_line((0, 2), (2, 0))

        sg4, = decomp.add_line((.5,.5), (0.6,0.6))
        decomp.new_segment(sg4.vtxs[0], pt0)
        assert len(decomp.wires) == 3


class TestPolygon:
    def test_polygon_depth(self):
        decomp = PolygonDecomposition()

        # outer square
        sg_a, = decomp.add_line((0,0), (2,0))
        sg_b, = decomp.add_line((2, 0), (2, 2))
        sg_c, = decomp.add_line((2, 2), (0, 2))
        sg_d, = decomp.add_line((0, 2), (0, 0))

        # inner square
        sg_e, = decomp.add_line((0.5, 0.5), (1, 0.5))
        sg_f, = decomp.add_line((1, 0.5), (1, 1))
        sg_g, = decomp.add_line((1, 1), (0.5, 1))
        sg_h, = decomp.add_line((0.5, 1), (0.5, 0.5))

        assert decomp.polygons[0].depth() == 0
        assert decomp.polygons[1].depth() == 2
        assert decomp.polygons[2].depth() == 4

class TestDecomposition:
    #
    # def plot_polygon(self, polygon):
    #     if polygon is None or polygon.displayed or polygon.outer_wire.is_root():
    #         return []
    #
    #     # recursion
    #     assert polygon.outer_wire.parent.polygon != polygon
    #     patches = self.plot_polygon( polygon.outer_wire.parent.polygon )
    #     pts = [ pt.xy for pt in polygon.vertices() ]
    #
    #     patches.append(mp.Polygon(pts))
    #     return patches
    #
    # def plot_polygons(self, decomp):
    #     fig, ax = plt.subplots()
    #
    #     # polygons
    #     for poly in decomp.polygons.values():
    #         poly.displayed = False
    #
    #     patches = []
    #     for poly in decomp.polygons.values():
    #         patches.extend( self.plot_polygon(poly) )
    #     p = mc.PatchCollection(patches, color='blue', alpha=0.2)
    #
    #     ax.add_collection(p)
    #
    #
    #     for s in decomp.segments.values():
    #         ax.plot((s.vtxs[0].xy[0], s.vtxs[1].xy[0]), (s.vtxs[0].xy[1], s.vtxs[1].xy[1]), color='green')
    #
    #     x_pts = []
    #     y_pts = []
    #     for pt in decomp.points.values():
    #         x_pts.append(pt.xy[0])
    #         y_pts.append(pt.xy[1])
    #     ax.plot(x_pts, y_pts, 'bo', color = 'red')
    #
    #     plt.show()


    def test_decomp(self):

        decomp = PolygonDecomposition()
        decomp.set_tolerance(0.01)
        outer = decomp.outer_polygon
        assert decomp.get_last_polygon_changes() == (PolygonChange.add, outer.id, outer.id)

        # test add point
        pt_a = decomp.add_point(  [0, 0] )
        assert pt_a.poly == outer
        pt_b = decomp.add_point( [1, 0] )
        assert pt_a.poly == outer

        # test snap to point
        pt = decomp.snap_point([0, 5e-3])
        assert pt == (0, pt_a, None)
        pt = decomp.snap_point([5e-3, 5e-3])
        assert pt == (0, pt_a, None)
        pt = decomp.snap_point([1+5e-3, 5e-3])
        assert pt == (0, pt_b, None)

        # test new_segment, new_wire
        sg_c = decomp.new_segment(pt_a, pt_b)
        assert len(decomp.polygons) == 1
        assert len(decomp.outer_polygon.outer_wire.childs) == 1
        assert decomp.get_last_polygon_changes() == (PolygonChange.none, None, None)


        # test line matching existing segment
        sg_c = decomp.new_segment(pt_a, pt_b)
        sg_c = decomp.new_segment(pt_b, pt_a)

        # test add_line - new_segment, add_dendrite
        res = decomp.add_line( (0,0), (0,1) )
        assert len(res) == 1
        sg_d = res[0]
        assert sg_d.next[left_side] == (sg_d, right_side)
        assert sg_d.next[right_side] == (sg_c, left_side)
        assert sg_c.next[left_side] == (sg_c, right_side)
        assert sg_c.next[right_side] == (sg_d, left_side)
        assert pt_a.poly == None
        assert pt_a.segment == (sg_c, out_vtx)
        assert decomp.get_last_polygon_changes() == (PolygonChange.shape, [outer.id], None)

        res = decomp.add_line( (2,0), (3,1) )
        sg_x, = res
        assert len(decomp.polygons) == 1
        assert len(decomp.outer_polygon.outer_wire.childs) == 2


        # test snap point - snap to line
        pt = decomp.snap_point([0.5, 5e-3])
        assert pt == (1, sg_c, 0.5)
        pt = decomp.snap_point([5e-3, 0.3])
        assert pt == (1, sg_d, 0.3)
        pt = decomp.snap_point([1+5e-3, 5e-3])
        assert pt == (0, pt_b, None)

        print(decomp)
        # test _split_segment, new segment - add_dendrite
        result = decomp.add_line((2,1), (3,0))
        sg_e, sg_f = result
        assert decomp.get_last_polygon_changes() == (PolygonChange.shape, [outer.id], None)

        assert sg_e.vtxs[out_vtx].colocated((2,1), 0.001)
        assert sg_e.vtxs[in_vtx].colocated((2.5, 0.5), 0.001)
        assert sg_f.vtxs[out_vtx].colocated((2.5, 0.5), 0.001)
        assert sg_f.vtxs[in_vtx].colocated((3, 0), 0.001)

        assert sg_e.next[right_side] == (sg_e, left_side)
        sg_h = sg_e.next[left_side][0]
        assert sg_e.next[left_side] == (sg_h, left_side)
        assert sg_h.next[left_side] == (sg_h, right_side)
        assert sg_h.next[right_side] == (sg_f, left_side)
        assert sg_f.next[left_side] == (sg_f, right_side)
        sg_g = sg_f.next[right_side][0]
        assert sg_f.next[right_side] == (sg_g, right_side)
        assert sg_g.next[right_side] == (sg_g, left_side)
        assert sg_g.next[left_side] == (sg_e, right_side)
        sg_o, sg_p = decomp.add_line((2.5, 0), (3, 0.5))

        # test add_point on segment
        decomp.add_point((2.25, 0.75))
        #plot_polygon_decomposition(decomp)


        # test new_segment - split polygon
        decomp.add_line( (-0.5, 1), (0.5, 0))
        assert decomp.get_last_polygon_changes() == (PolygonChange.add, outer.id, 1)

        # test split_segment in vertex
        decomp.add_line( (2,0.5), (2,-0.5))

        # test new_segment - join_wires
        assert len(decomp.wires) == 4
        assert len(decomp.polygons) == 2

        print(decomp)
        #plot_polygon_decomposition(decomp)
        sg_m, = decomp.add_line((0, 1), (2, 1))
        print(decomp)



        assert len(decomp.wires) == 3
        assert len(decomp.polygons) == 2
        assert decomp.get_last_polygon_changes() == (PolygonChange.shape, [outer.id], None)

        #plot_polygon_decomposition(decomp)

        # delete segment - split wire
        decomp.delete_segment(sg_m)
        assert len(decomp.wires) == 4
        assert len(decomp.polygons) == 2
        #plot_polygon_decomposition(decomp)
        assert decomp.get_last_polygon_changes() == (PolygonChange.shape, [outer.id], None)

        # other split wire
        pt_op = sg_p.vtxs[out_vtx]
        decomp.delete_segment(sg_f)
        assert len(decomp.wires) == 5
        assert len(decomp.polygons) == 2
        #plot_polygon_decomposition(decomp)

        #test split_segment connected on both sides; split non outer polygon
        seg_y, = decomp.add_line( (0,0.25), (0.25, 0.25))
        assert decomp.get_last_polygon_changes() == (PolygonChange.split, 1, 2)

        # test _join_segments - _split_segment inversion
        seg1 = sg_e
        mid_point = seg1.vtxs[in_vtx]
        seg0 = sg_e.next[left_side][0]
        decomp._join_segments(mid_point, seg0, seg1)

        # print("Decomp:\n", decomp)
        decomp.delete_point(pt_op)
        # plot_polygon_decomposition(decomp)

        # test join polygons
        decomp.delete_segment(seg_y)
        assert decomp.get_last_polygon_changes() == (PolygonChange.join, 1, 2)

        # test add_free_point
        decomp.add_free_point(100, (3.0, 0.3), decomp.outer_polygon.id)
        decomp.remove_free_point(100)


    def check_split_poly_structure(self, decomp, out_square, in_square):
        decomp.check_consistency()

        sg_a, sg_b, sg_c, sg_d = out_square
        sg_e, sg_f, sg_g, sg_h = in_square

        assert sg_b.wire == sg_a.wire
        assert sg_c.wire == sg_a.wire
        assert sg_d.wire == sg_a.wire

        assert sg_f.wire == sg_e.wire
        assert sg_g.wire == sg_e.wire
        assert sg_h.wire == sg_e.wire

        wire1 = decomp.outer_polygon.outer_wire
        wire2 = list(wire1.childs)[0]
        wire3 = list(wire2.childs)[0]
        assert sg_a.wire == [wire2, wire3]
        wire4 = list(wire3.childs)[0]
        wire5 = list(wire4.childs)[0]
        assert sg_e.wire == [wire4, wire5]
        assert len(wire5.childs) == 0





    def test_split_poly(self):

        decomp = PolygonDecomposition()
        sg_a, = decomp.add_line((0,0), (2,0))
        sg_b, = decomp.add_line((2, 0), (2, 2))
        sg_c, = decomp.add_line((2, 2), (0, 2))
        sg_d, = decomp.add_line((0, 2), (0, 0))
        # closed outer polygon


        assert sg_a.next == [ (sg_d, 0), (sg_b, 1)]
        assert sg_b.next == [ (sg_a, 0), (sg_c, 1)]
        assert sg_c.next == [ (sg_b, 0), (sg_d, 1)]
        assert sg_d.next == [ (sg_c, 0), (sg_a, 1)]

        external_wire = list(decomp.outer_polygon.outer_wire.childs)[0]
        assert sg_a.wire[right_side] == external_wire
        assert sg_b.wire[right_side] == external_wire
        assert sg_c.wire[right_side] == external_wire
        assert sg_d.wire[right_side] == external_wire
        #plot_polygon_decomposition(decomp)

        assert len(decomp.polygons) == 2
        sg_e, = decomp.add_line((0.5, 0.5), (1, 0.5))
        sg_f, = decomp.add_line((1, 0.5), (1, 1))
        sg_g, = decomp.add_line((1, 1), (0.5, 1))
        sg_h, = decomp.add_line((0.5, 1), (0.5, 0.5))
        # closed inner polygon
        #plot_polygon_decomposition(decomp)
        print("Decomp:\n", decomp)
        out_square = sg_a, sg_b, sg_c, sg_d
        in_square = sg_e, sg_f, sg_g, sg_h
        self.check_split_poly_structure(decomp, out_square, in_square)

        # join nested wires
        sg_x = decomp.new_segment( sg_a.vtxs[out_vtx], sg_e.vtxs[out_vtx] )

        # split nested wires
        decomp.delete_segment(sg_x)
        self.check_split_poly_structure(decomp, out_square, in_square)


        # split polygon - balanced
        seg_y, = decomp.add_line((0.5, 0.5), (1,1))

        # join polygons - balanced
        decomp.delete_segment(seg_y)
        self.check_split_poly_structure(decomp, out_square, in_square)

        # join nested polygons
        decomp.delete_segment(sg_h)
        #plot_polygon_decomposition(decomp)
        assert sg_b.wire == sg_a.wire
        assert sg_c.wire == sg_a.wire
        assert sg_d.wire == sg_a.wire

        assert sg_f.wire == sg_e.wire
        assert sg_g.wire == sg_e.wire
        assert sg_h.wire == sg_e.wire
        we_r, we_l = sg_e.wire
        assert we_r == we_l

        wire1 = decomp.outer_polygon.outer_wire
        wire2 = list(wire1.childs)[0]
        wire3 = list(wire2.childs)[0]
        assert sg_a.wire == [wire2, wire3]
        wire4 = list(wire3.childs)[0]
        assert we_r == wire4
        assert len(wire4.childs) == 0


    def test_seg_add_remove(self):
        decomp = PolygonDecomposition()
        decomp.add_line((0, 1), (0,0))
        decomp.add_line((0, 0), (1, 0))
        seg_c, = decomp.add_line((1, 0), (0, 1))

        decomp.add_line((1, 0), (2, 0))
        decomp.add_line((2, 0), (2, 1))
        decomp.add_line((1, 0), (2, 1) )
        #plot_polygon_decomposition(decomp)
        assert len(decomp.outer_polygon.outer_wire.childs) == 1
        assert len(decomp.outer_polygon.outer_wire.childs.pop().childs) == 2

        decomp.delete_segment(seg_c)
        #plot_polygon_decomposition(decomp)

    def test_split_poly_1(self):
        # Test splitting of points and holes.
        decomp = PolygonDecomposition()
        decomp.add_line((0, 0), (1,0))
        decomp.add_line((0, 0), (0, 1))
        decomp.add_line((1, 1), (1, 0))
        decomp.add_line((1, 1), (0, 1))
        decomp.add_point( (0.2,0.2))
        decomp.add_point( (0.8, 0.2))
        decomp.add_line((0.2, 0.6), (0.3,0.6))
        decomp.add_line((0.8, 0.6), (0.7, 0.6))
        #plot_polygon_decomposition(decomp)
        decomp.add_line((0.5,0), (0.5,1))
        #plot_polygon_decomposition(decomp)


    def test_join_poly(self):
        decomp = PolygonDecomposition()
        sg0, = decomp.add_line((0, 0), (0, 2))
        decomp.add_line((0, 0), (2, 0))
        sg2, = decomp.add_line((0, 2), (2, 0))
        decomp.delete_segment(sg2)

    def test_make_indices(self):
        decomp = PolygonDecomposition()
        sg0, = decomp.add_line((0, 0), (0, 2))
        decomp.add_line((0, 0), (2, 0))
        sg2, = decomp.add_line((0, 2), (2, 0))
        decomp.make_indices()
        assert sg2.index == 2
        assert decomp.polygons[0].index == 0
        assert decomp.polygons[1].index == 1

    def test_check_displacement(self):
        decomp = PolygonDecomposition()
        sg, = decomp.add_line((0, 0), (0, 2))
        pt0 = sg.vtxs[0]
        decomp.add_line((0, 0), (2, 0))
        decomp.add_line((0, 2), (2, 0))
        pt = decomp.add_point((.5,.5))
        decomp.add_line((0, 0), (.5,.5))
        decomp.add_line((2, 0), (.5,.5))
        decomp.add_line( (.5,.5), (0, 2))

        step = decomp.check_displacment([pt0, pt], (1.0, 1.0), 0.1)
        assert la.norm( step - np.array([0.45, 0.45]) ) < 1e-6
        assert decomp.get_last_polygon_changes() == (PolygonChange.shape, [0,1,2,3], None)

        decomp.move_points([pt], step)
        assert la.norm( pt.xy - np.array([0.95, 0.95]) ) < 1e-6

        step = decomp.check_displacment([pt], (1.0, 1.0), 0.1)
        assert decomp.get_last_polygon_changes() == (PolygonChange.shape, [1,2,3], None)


    def test_join_segments(self):
        decomp = PolygonDecomposition()
        sg0, = decomp.add_line((0,0), (1,0))
        mid_pt = sg0.vtxs[1]
        sg1, = decomp.add_line((2,0), (1,0))
        sg2, = decomp.add_line((2, 0), (3, 0))
        decomp._join_segments(sg0.vtxs[1], sg0, sg1)
        decomp._join_segments(sg0.vtxs[1], sg0, sg2)



    def test_join_polygons_embedded(self):
        decomp = PolygonDecomposition()
        decomp.add_line((0, 0), (3, 0))
        decomp.add_line((0, 0), (0, 3))
        sg3, = decomp.add_line((0, 3), (3, 0))
        decomp.delete_segment(sg3)
        assert len(decomp.outer_polygon.outer_wire.childs) == 1
        wire = list(decomp.outer_polygon.outer_wire.childs)[0]
        assert len(wire.childs) == 0


    def test_polygon_childs_degenerate(self):
        decomp = PolygonDecomposition()
        decomp.add_line((0, 0), (3, 0))
        decomp.add_line((0, 0), (0, 3))
        decomp.add_line((0, 3), (3, 0))
        decomp.add_line((1, 1), (2, 1))
        decomp.add_line((1, 1), (1, 2))
        decomp.add_line((1, 2), (2, 1))
        #plot_polygon_decomposition(decomp)

        decomp.add_line((1, 1), (0, 0))
        decomp.add_line((2, 1), (3, 0))
        decomp.add_line((1, 2), (0, 3))
        #plot_polygon_decomposition(decomp)

    def test_polygon_childs(self):
        decomp = PolygonDecomposition()
        decomp.add_line((0, 0), (4, 0))
        decomp.add_line((0, 0), (0, 4))
        decomp.add_line((0, 4), (4, 0))
        decomp.add_line((1, 1), (2, 1))
        decomp.add_line((1, 1), (1, 2))
        decomp.add_line((1, 2), (2, 1))
        #plot_polygon_decomposition(decomp)
        lst = list(decomp.get_childs(0))
        assert lst == [0,1,2]

        decomp.add_line((1, 1), (0, 0))
        decomp.add_line((2, 1), (4, 0))
        decomp.add_line((1, 2), (0, 4))
        #plot_polygon_decomposition(decomp)


    def test_add_dendrite(self):
       decomp = PolygonDecomposition()
       pt0 = decomp.add_point( (31.6, -40) )
       pt1 = decomp.add_point( (32.4, -62.8) )
       pt2 = decomp.add_point( (57.7, -37.4) )
       decomp.new_segment(pt0, pt1)
       decomp.new_segment(pt0, pt2)
       decomp.new_segment(pt1, pt2)
       # print(decomp)
       pt3 = decomp.add_free_point(4, (75.7, -35), 0 )
       decomp.new_segment(pt2, pt3)
       #plot_polygon_decomposition(decomp)


    def test_simple_intersections(self):
        da = PolygonDecomposition()
        da.add_line((0, 0), (1,0))
        da.add_line((0, 0), (0, 1))
        da.add_line((1, 1), (1, 0))
        da.add_line((1, 1), (0, 1))
        da.add_line((0, 0), (1, 1))
        print("da:\n", da)

        db = PolygonDecomposition()
        db.add_line((0, 0), (1,0))
        db.add_line((0, 0), (0, 1))
        db.add_line((1, 1), (1, 0))
        db.add_line((1, 1), (0, 1))
        db.add_line((1, 0), (0, 1))
        print("db:\n", db)

        (dc, maps_a, maps_b) = da.intersection(db)
        print("dc\n", dc)
        #plot_polygon_decomposition(dc)
        assert maps_a[0] == { 0: 0, 1: 1, 2: 2, 3: 3}
        assert maps_b[0] == { 0: 0, 1: 1, 2: 2, 3: 3}
        assert maps_a[1] == { 0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5:4, 6:None, 7:None}
        assert maps_b[1] == { 0: 0, 1: 1, 2: 2, 3: 3, 4: None, 5:None, 6:4, 7:4}
        assert maps_a[2] == { 0: 0, 1: 1, 2: 2, 3: 1, 4: 2}
        assert maps_b[2] == { 0: 0, 1: 1, 2: 1, 3: 2, 4: 2}

    def test_complex_wire_remove(self):
        da = PolygonDecomposition()
        # outer triangle
        da.add_line((0, 4), (0,0))
        da.add_line((0, 0), (4, 0))
        da.add_line((4, 0), (0, 4))

        # inner triangle
        da.add_line((1, 2), (1, 1))
        da.add_line((1, 1), (2, 1))
        da.add_line((2, 1), (1, 2))

        # rugs
        sa, = da.add_line((2, 1), (4, 0))
        sb, = da.add_line((1, 2), (0, 4))

        print("initial dc:\n", da)
        #plot_polygon_decomposition(da)

        da.delete_segment(sb)
        da.delete_segment(sa)
        print("final dc:\n", da)