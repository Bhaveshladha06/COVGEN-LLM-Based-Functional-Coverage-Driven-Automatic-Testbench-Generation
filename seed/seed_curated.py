"""The six examples supplied with the project (from the reference PDF).

Corrected where irun 15.20 rejected them:
  * mux2 / mux4 / decoder2to4 used their own covergroup arguments inside
    the @(...) sampling event, which is *E,EFASAM. The event is removed;
    the testbench calls .sample() explicitly instead.
  * decoder2to4 had `ignore_bins ... = default;` inside a cross that also
    defines its own bins, which is *E,ECBNOD.
  * unlabelled crosses in full_adder and adder8 were given labels.
"""

E = []


def add(eid, dtype, width, module, signals, req, rtl, cg):
    E.append(dict(id=eid, design_context=dict(module=module, data_width=width, type=dtype),
                  signals=signals, english_requirement=req, rtl=rtl, coverage_model=cg))


add('mux2_1bit_001', '2-to-1 multiplexer', 1, 'MUX2',
    ['a', 'b', 'sel', 'y'],
    'Cover 2-to-1 multiplexer behavior for all combinations of select and input values.',
    """module mux2(a, b, sel, y);
  input a, b, sel;
  output y;
  assign y = sel ? b : a;
endmodule""",
    """covergroup cg_mux2 (ref logic a, b, sel);
  sel_cp : coverpoint sel {
    bins sel_0 = {0};
    bins sel_1 = {1};
  }

  ab_cp : coverpoint {a, b} {
    bins ab_00 = {2'b00};
    bins ab_01 = {2'b01};
    bins ab_10 = {2'b10};
    bins ab_11 = {2'b11};
  }

  sel_x_ab : cross sel_cp, ab_cp;
endgroup""")

add('mux4_1bit_001', '4-to-1 multiplexer', 4, 'MUX4',
    ['d', 'sel', 'y'],
    'Cover 4-to-1 multiplexer behavior for all select values, input bit toggling, and output value per select combination.',
    """module mux4(d, sel, y);
  input [3:0] d;
  input [1:0] sel;
  output reg y;

  always @(*) begin
    case(sel)
      2'b00: y = d[0];
      2'b01: y = d[1];
      2'b10: y = d[2];
      2'b11: y = d[3];
    endcase
  end
endmodule""",
    """covergroup cg_mux4 (ref logic [3:0] d, ref logic [1:0] sel, ref logic y);

  sel_cp : coverpoint sel {
    bins sel_0 = {2'b00};
    bins sel_1 = {2'b01};
    bins sel_2 = {2'b10};
    bins sel_3 = {2'b11};
  }

  // toggle-style coverage: did each input bit ever see 0 and 1?
  d0_cp : coverpoint d[0];
  d1_cp : coverpoint d[1];
  d2_cp : coverpoint d[2];
  d3_cp : coverpoint d[3];

  // functional coverage: for each sel, did y see both values?
  y_cp : coverpoint y {
    bins y_0 = {0};
    bins y_1 = {1};
  }

  sel_x_y : cross sel_cp, y_cp;   // 4 x 2 = 8 meaningful bins

endgroup""")

add('full_adder_1bit_001', '1-bit full adder', 1, 'FULL_ADDER',
    ['a', 'b', 'cin', 'sum', 'cout'],
    'Cover full adder behavior for all combinations of inputs a, b, cin and resulting sum, cout outputs.',
    """module full_adder(a, b, cin, sum, cout);
  input a, b, cin;
  output sum, cout;

  assign {cout, sum} = a + b + cin;
endmodule""",
    """covergroup cg_fa (ref logic a, b, cin, sum, cout);

  // Input combinations
  cp_inputs: coverpoint {a,b,cin};

  // Output coverage
  cp_sum:  coverpoint sum;
  cp_cout: coverpoint cout;

  // Cross to relate inputs & outputs
  cp_in_out: cross cp_inputs, cp_sum, cp_cout;

endgroup""")

add('adder8_8bit_001', '8-bit adder', 8, 'ADDER8',
    ['a', 'b', 'sum'],
    'Cover 8-bit adder behavior across low, mid, and high value ranges for inputs a, b and resulting sum, including boundary and overflow conditions.',
    """module adder8(a, b, sum);
  input [7:0] a, b;
  output [7:0] sum;

  assign sum = a + b;
endmodule""",
    """covergroup cg_adder8 (ref logic [7:0] a, b, sum);

  cp_a: coverpoint a {
    bins low  = {[0:10]};
    bins mid  = {[11:244]};
    bins high = {[245:255]};
  }

  cp_b: coverpoint b {
    bins low  = {[0:10]};
    bins mid  = {[11:244]};
    bins high = {[245:255]};
  }

  cp_sum: coverpoint sum {
    bins zero = {0};
    bins max  = {255};
    bins mid  = {[1:254]};
  }

  cp_a_b_sum: cross cp_a, cp_b, cp_sum;

endgroup""")

add('prio_enc_4bit_001', '4-bit priority encoder', 4, 'PRIO_ENC',
    ['d', 'y'],
    'Cover 4-bit priority encoder behavior for all priority levels of input d and corresponding encoded output y, including cross coverage of legal input-output combinations.',
    """module prio_enc(d, y);
  input [3:0] d;
  output reg [1:0] y;

  always @(*) begin
    casex(d)
      4'b1xxx: y = 2'b11;
      4'b01xx: y = 2'b10;
      4'b001x: y = 2'b01;
      default: y = 2'b00;
    endcase
  end
endmodule""",
    """covergroup cg_pe (ref logic [3:0] d, ref logic [1:0] y);

  cp_d: coverpoint d {
    wildcard bins p3 = {4'b1???};   // d[3]=1 -> highest priority
    wildcard bins p2 = {4'b01??};   // d[3:2]=01
    wildcard bins p1 = {4'b001?};   // d[3:1]=001
    wildcard bins p0 = {4'b000?};   // d[3:1]=000 (covers 0000 and 0001)
  }

  cp_y: coverpoint y {
    bins y3 = {2'b11};
    bins y2 = {2'b10};
    bins y1 = {2'b01};
    bins y0 = {2'b00};
  }

  cross_dy: cross cp_d, cp_y {
    bins p3_y11 = binsof(cp_d.p3) && binsof(cp_y.y3);
    bins p2_y10 = binsof(cp_d.p2) && binsof(cp_y.y2);
    bins p1_y01 = binsof(cp_d.p1) && binsof(cp_y.y1);
    bins p0_y00 = binsof(cp_d.p0) && binsof(cp_y.y0);

    // explicitly drop every other combination - they can never occur
    ignore_bins illegal_combos =
        (binsof(cp_d.p3) && !binsof(cp_y.y3)) ||
        (binsof(cp_d.p2) && !binsof(cp_y.y2)) ||
        (binsof(cp_d.p1) && !binsof(cp_y.y1)) ||
        (binsof(cp_d.p0) && !binsof(cp_y.y0));
  }

endgroup""")

add('decoder2to4_2bit_001', '2-to-4 decoder', 2, 'DECODER2TO4',
    ['sel', 'y'],
    'Cover 2-to-4 decoder behavior for all select values and the corresponding one-hot output, treating non-one-hot outputs as illegal.',
    """module decoder2to4(sel, y);
  input [1:0] sel;
  output [3:0] y;

  assign y = 4'b0001 << sel;
endmodule""",
    """covergroup cg_dec (ref logic [1:0] sel, ref logic [3:0] y);
  sel_cp: coverpoint sel {
    bins sel_0 = {2'b00};
    bins sel_1 = {2'b01};
    bins sel_2 = {2'b10};
    bins sel_3 = {2'b11};
  }

  y_cp: coverpoint y {
    bins onehot[] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
    illegal_bins invalid = default;
  }

  c_sel_y : cross sel_cp, y_cp {
    bins sel0_y1 = binsof(sel_cp.sel_0) && binsof(y_cp) intersect {4'b0001};
    bins sel1_y2 = binsof(sel_cp.sel_1) && binsof(y_cp) intersect {4'b0010};
    bins sel2_y4 = binsof(sel_cp.sel_2) && binsof(y_cp) intersect {4'b0100};
    bins sel3_y8 = binsof(sel_cp.sel_3) && binsof(y_cp) intersect {4'b1000};
  }
endgroup""")
