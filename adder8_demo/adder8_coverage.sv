`timescale 1ns/1ps
// Coverage model, written in exactly the shape the pipeline produces:
//   - a module wrapping the covergroup (a bare covergroup is *E,UPITEM on irun 15.20)
//   - the covergroup takes NO arguments; it reads the module's ports directly
//   - option.per_instance = 1  <-- without this IMC records nothing at all
//   - every coverpoint and cross LABELLED (*E,ECGECL otherwise)
//   - a final block printing the score, so the number does not depend on IMC
//
// COMBINATIONAL DUT, so there is NO @(...) on the covergroup. It is sampled by
// an explicit .sample() call one time unit after the inputs change -- see the
// always block below for why that delay matters.
module adder8_coverage (
  input logic [7:0] a,
  input logic [7:0] b,
  input logic       cin,
  input logic [7:0] sum,
  input logic       cout
);

  covergroup adder8_cg;          // no sampling event -- see the always block below
    option.per_instance = 1;

    // 8 bits = 256 values. Bucket them instead of enumerating: boundary values
    // get their own bin, the rest are grouped into ranges.
    a_cp : coverpoint a {
      bins zero = {8'd0};
      bins low  = {[8'd1   : 8'd63 ]};
      bins mid  = {[8'd64  : 8'd191]};
      bins high = {[8'd192 : 8'd254]};
      bins max  = {8'd255};
    }

    b_cp : coverpoint b {
      bins zero = {8'd0};
      bins low  = {[8'd1   : 8'd63 ]};
      bins mid  = {[8'd64  : 8'd191]};
      bins high = {[8'd192 : 8'd254]};
      bins max  = {8'd255};
    }

    cin_cp : coverpoint cin {
      bins clear = {1'b0};
      bins set   = {1'b1};
    }

    sum_cp : coverpoint sum {
      bins zero = {8'd0};
      bins low  = {[8'd1   : 8'd63 ]};
      bins mid  = {[8'd64  : 8'd191]};
      bins high = {[8'd192 : 8'd254]};
      bins max  = {8'd255};
    }

    cout_cp : coverpoint cout {
      bins clear = {1'b0};
      bins set   = {1'b1};
    }

    // 5 x 5 = 25 combinations of the two operand ranges.
    a_x_b : cross a_cp, b_cp;

    // 2 x 2 = 4. All four are reachable: carry-out depends on the sum, not on
    // carry-in alone, so cin can be either value with cout either value.
    cin_x_cout : cross cin_cp, cout_cp;

  endgroup

  adder8_cg cg_inst = new();

  // Sample AFTER the outputs have settled.
  //
  // Writing `covergroup adder8_cg @(a or b or cin);` instead looks equivalent and
  // is not. That event fires in the same simulation region as the DUT's
  // `assign {cout, sum} = a + b + cin;`, and the LRM does not order them -- so
  // sum_cp and cout_cp can sample the PREVIOUS vector's outputs. Every bin still
  // gets hit eventually, so the score still reads 100%: the error is invisible in
  // the percentage and only shows up as bins credited to the wrong input.
  //
  // The #1 delay lets the continuous assignment settle first. The testbench
  // leaves #10 between vectors, so there is plenty of room.
  always @(a or b or cin) begin
    #1 cg_inst.sample();
  end

  final begin
    $display("SV_FUNCTIONAL_COVERAGE: %0.4f", $get_coverage());
    $display("SV_CP a_cp      : %0.4f", cg_inst.a_cp.get_coverage());
    $display("SV_CP b_cp      : %0.4f", cg_inst.b_cp.get_coverage());
    $display("SV_CP cin_cp    : %0.4f", cg_inst.cin_cp.get_coverage());
    $display("SV_CP sum_cp    : %0.4f", cg_inst.sum_cp.get_coverage());
    $display("SV_CP cout_cp   : %0.4f", cg_inst.cout_cp.get_coverage());
    $display("SV_CP a_x_b     : %0.4f", cg_inst.a_x_b.get_coverage());
    $display("SV_CP cin_x_cout: %0.4f", cg_inst.cin_x_cout.get_coverage());
  end

endmodule
