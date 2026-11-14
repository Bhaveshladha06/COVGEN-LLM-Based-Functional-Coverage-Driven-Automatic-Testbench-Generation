`timescale 1ns/1ps
module adder16_coverage (
  input logic [15:0] a,
  input logic [15:0] b,
  input logic        cin,
  input logic [15:0] sum,
  input logic        cout
);

  // All declarations go at the TOP of a begin...end block, before any statement.
  // No local variables are needed for this coverage model.

  covergroup adder16_coverage_cg @(a or b or cin);
    option.per_instance = 1;

    // Input 'a' ranges: low, mid, high.
    // The maximum value for a 16-bit unsigned input is 2^16 - 1 = 65535.
    a_cp : coverpoint a {
      bins low  = {[0:100]};
      bins mid  = {[101:65434]};
      bins high = {[65435:65535]};
    }

    // Input 'b' ranges: low, mid, high.
    // The maximum value for a 16-bit unsigned input is 2^16 - 1 = 65535.
    b_cp : coverpoint b {
      bins low  = {[0:100]};
      bins mid  = {[101:65434]};
      bins high = {[65435:65535]};
    }

    // Carry-in signal: cover both states (0 and 1).
    cin_cp : coverpoint cin {
      bins zero = {0};
      bins one  = {1};
    }

    // Output 'sum' ranges: zero, mid, max.
    // The 'sum' output is 16-bit, so its maximum value is 2^16 - 1 = 65535.
    // The RTL `assign {cout, sum} = a + b + cin;` confirms 'sum' can take any value
    // within its 16-bit range, and 'cout' captures overflow.
    sum_cp : coverpoint sum {
      bins zero = {0};
      bins mid  = {[1:65534]};
      bins max  = {65535};
    }

    // Carry-out signal: cover both states (0 and 1).
    cout_cp : coverpoint cout {
      bins zero = {0};
      bins one  = {1};
    }

    // Cross the input ranges against the carry-out to confirm overflow is exercised.
    // Overflow (cout=1) occurs when a + b + cin >= 2^16 (65536).
    // We must prune unreachable cross bins where cout=1 but the inputs are too small.
    // Max sum for a_cp.low + b_cp.low + cin = 100 + 100 + 1 = 201. This is < 65536.
    // Max sum for a_cp.low + b_cp.mid + cin = 100 + 65434 + 1 = 65535. This is < 65536.
    // Max sum for a_cp.mid + b_cp.low + cin = 65434 + 100 + 1 = 65535. This is < 65536.
    a_b_cout_x : cross a_cp, b_cp, cout_cp {
      ignore_bins low_a_low_b_cout_1 = binsof(a_cp.low) && binsof(b_cp.low) && binsof(cout_cp.one);
      ignore_bins low_a_mid_b_cout_1 = binsof(a_cp.low) && binsof(b_cp.mid) && binsof(cout_cp.one);
      ignore_bins mid_a_low_b_cout_1 = binsof(a_cp.mid) && binsof(b_cp.low) && binsof(cout_cp.one);
    }

  endgroup

  adder16_coverage_cg cg_inst = new();

  // Report the covergroup score directly from the simulator, so the
  // number does not depend on the coverage database or IMC's flags.
  final begin
    $display("SV_FUNCTIONAL_COVERAGE: %0.4f", $get_coverage());
    $display("SV_CG_INST_COVERAGE: %0.4f", cg_inst.get_inst_coverage());
  end

endmodule