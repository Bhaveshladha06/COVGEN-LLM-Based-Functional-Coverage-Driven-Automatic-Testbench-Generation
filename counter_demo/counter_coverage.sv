`timescale 1ns/1ps
// The coverage model. Hand-written for this demo so the result is identical
// every time -- nothing here comes from the LLM.
//
// The testbench deliberately only counts up to 5, so these bins CANNOT be hit:
//     count_cp.high        (8..14)
//     count_cp.max         (15)
//     wrap_cp.wrap         (15 => 0)
//     count_x_en           any pair involving high or max
// Everything else should be hit. Check the reports against that list.
module counter_coverage (
  input logic       clk,
  input logic       rst_n,
  input logic       en,
  input logic [3:0] count
);

  covergroup counter_cg @(posedge clk);
    option.per_instance = 1;   // WITHOUT THIS, IMC RECORDS NOTHING. See step 6.

    count_cp : coverpoint count {
      bins zero = {4'd0};
      bins low  = {[4'd1 : 4'd7]};
      bins high = {[4'd8 : 4'd14]};
      bins max  = {4'd15};
    }

    en_cp : coverpoint en {
      bins off = {1'b0};
      bins on  = {1'b1};
    }

    rst_cp : coverpoint rst_n {
      bins asserted   = {1'b0};
      bins deasserted = {1'b1};
    }

    // A transition bin: 15 followed by 0, only counted while enabled.
    wrap_cp : coverpoint count iff (en) {
      bins wrap = (4'd15 => 4'd0);
    }

    // 4 count bins x 2 en bins = 8 combinations.
    count_x_en : cross count_cp, en_cp;

  endgroup

  counter_cg cg_inst = new();

  final begin
    $display("SV_FUNCTIONAL_COVERAGE: %0.4f", $get_coverage());
    $display("SV_CP count_cp : %0.4f", cg_inst.count_cp.get_coverage());
    $display("SV_CP en_cp    : %0.4f", cg_inst.en_cp.get_coverage());
    $display("SV_CP rst_cp   : %0.4f", cg_inst.rst_cp.get_coverage());
    $display("SV_CP wrap_cp  : %0.4f", cg_inst.wrap_cp.get_coverage());
    $display("SV_CP cross    : %0.4f", cg_inst.count_x_en.get_coverage());
  end

endmodule
