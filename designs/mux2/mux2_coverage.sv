`timescale 1ns/1ps
module mux2_coverage (
  input logic a,
  input logic b,
  input logic sel
);

  // The DUT is combinational, so the covergroup has no sampling event.
  // It will be sampled explicitly one time unit after inputs change.
  covergroup mux2_coverage_cg;
    option.per_instance = 1;

    // RTL analysis: 'a', 'b', and 'sel' are 1-bit inputs.
    // They can only take values 0 or 1.
    // The bins reflect these two possible values for each signal.
    a_cp : coverpoint a {
      bins a_is_0 = {0};
      bins a_is_1 = {1};
    }

    b_cp : coverpoint b {
      bins b_is_0 = {0};
      bins b_is_1 = {1};
    }

    sel_cp : coverpoint sel {
      bins sel_is_0 = {0}; // Selects 'a'
      bins sel_is_1 = {1}; // Selects 'b'
    }

    // Requirement: "cross select against the input combinations."
    // All combinations of a, b, and sel are valid inputs for a mux.
    // There are 2*2*2 = 8 possible input combinations.
    sel_a_b_x : cross sel_cp, a_cp, b_cp;

  endgroup

  mux2_coverage_cg cg_inst = new();

  // Sample AFTER the outputs have settled, not at the instant the
  // inputs change. `@(a or b or sel)` on its own fires in the same region as
  // the DUT's continuous assignments, so the output coverpoints would
  // read the PREVIOUS vector's results -- a race that still reports
  // 100% while crediting the wrong bins.
  always @(a or b or sel) begin
    #1 cg_inst.sample();
  end

  // Report the covergroup score directly from the simulator, so the
  // number does not depend on the coverage database or IMC's flags.
  final begin
    $display("SV_FUNCTIONAL_COVERAGE: %0.4f", $get_coverage());
    $display("SV_CG_INST_COVERAGE: %0.4f", cg_inst.get_inst_coverage());
  end

endmodule