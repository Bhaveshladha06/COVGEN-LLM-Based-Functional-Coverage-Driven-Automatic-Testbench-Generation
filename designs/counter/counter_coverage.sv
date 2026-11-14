`timescale 1ns/1ps
module counter_coverage (
  input logic       clk,
  input logic       rst_n,
  input logic       en,
  input logic [3:0] count
);

  covergroup counter_coverage_cg @(posedge clk);
    option.per_instance = 1;

    // Counter range is 0 to 15 as per RTL (4-bit unsigned).
    count_cp : coverpoint count {
      bins zero = {4'h0};
      bins low  = {[4'h1:4'h7]};
      bins high = {[4'h8:4'hE]};
      bins max  = {4'hF}; // 15
    }

    en_cp : coverpoint en {
      bins disabled = {0};
      bins enabled  = {1};
    }

    rst_n_cp : coverpoint rst_n {
      bins asserted   = {0};
      bins deasserted = {1};
    }

    // Cover the counter reaching its maximum value (15) and wrapping around to 0
    // on the next *enabled* clock edge.
    // This coverpoint contains transition bins and must not appear in a cross.
    count_wrap_cp : coverpoint count iff (en) {
      bins wrap = (4'hF => 4'h0); // 15 => 0
    }

    // Cover the counter holding its value when en is *deasserted*,
    // including holding at 0 and holding at 15.
    // This coverpoint contains transition bins and must not appear in a cross.
    count_hold_cp : coverpoint count iff (!en) {
      bins hold_zero = (4'h0 => 4'h0);
      bins hold_max  = (4'hF => 4'hF); // 15 => 15
    }

    // Cover an asynchronous reset asserted both while the counter is counting (en=1)
    // and while it is held (en=0).
    rst_n_x_en : cross rst_n_cp, en_cp;

    // Cover an asynchronous reset asserted while the counter is in various states.
    // When rst_n is asserted (0), the RTL forces 'count' to 0.
    // Therefore, any combination of rst_n.asserted with count != 0 is unreachable
    // *during* reset and must be pruned.
    rst_n_x_count : cross rst_n_cp, count_cp {
      ignore_bins reset_active_non_zero = binsof(rst_n_cp.asserted) && !binsof(count_cp.zero);
    }

  endgroup

  counter_coverage_cg cg_inst = new();

  // Report the covergroup score directly from the simulator, so the
  // number does not depend on the coverage database or IMC's flags.
  final begin
    $display("SV_FUNCTIONAL_COVERAGE: %0.4f", $get_coverage());
    $display("SV_CG_INST_COVERAGE: %0.4f", cg_inst.get_inst_coverage());
  end

endmodule