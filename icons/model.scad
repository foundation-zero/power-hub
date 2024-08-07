file = "./svgs/pv.svg";
scale = 9;
base_diameter = 150;
base_height = 10;
base = 130;
icon_height = 10;
icon_depth = 5;
render_front = true;
render_base = true;
anchor_hole_thickness = 3;
anchor_hole_depth = 5;
anchor_hole_width = 20;
right_arrow = false;
left_arrow = false;


$fn = 100;

function icon_offset() = right_arrow || left_arrow ? 10 : 0;

module arrow(offset) {
    translate([0, -(base_diameter * 0.5 - 20), 0])
    offset(r=offset)
    scale(8)
    polygon([
      [-1.75, -.75],
      [1, -.75],
      [1, -1.5],
      [2.5, 0],
      [1, 1.5],
      [1, .75],
      [-1.75, .75]]);
}

module base() {
    union() {
        difference() {
            cylinder(h=base_height, d = base_diameter);
            front(offset=0.4);
            translate([base_diameter * 0.5 - 20, 0, 0])
            anchor();
        translate([-(base_diameter * 0.5 - 20), 0, 0])
            anchor();
        };
        
    }
}

module anchor() {
    rotate(a=90, v=[0, 0, 1])
    translate([0, 0, -5])
    union() {
        rotate(a=45, v=[1, 0, 0])
        translate([0, anchor_hole_width * 0.5 - anchor_hole_thickness * 0.5, 0])
        cube([anchor_hole_depth, anchor_hole_thickness, anchor_hole_width], center=true);
        rotate(a=-45, v=[1, 0, 0])
        translate([0, -(anchor_hole_width * 0.5 - anchor_hole_thickness * 0.5), 0])
        cube([anchor_hole_depth, anchor_hole_thickness, anchor_hole_width], center=true);

    }
}

module front(offset=offset) {
    translate([0, 0, icon_depth])
    linear_extrude(height=icon_height)
    union() {
        translate([0, icon_offset(), 0])
        offset(r=offset)
        scale([scale, scale, 1])
        import(file, center = true);
        
        if (right_arrow) {
            arrow(offset=offset);
        }
        if (left_arrow) {
            scale([-1, 1, 1])
            arrow(offset=offset);
        }
    }
}

if (render_base) {
    color("#dddddd")
    base();
}
if (render_front) {
    color("#dd0000")
    front(offset=0);
}

