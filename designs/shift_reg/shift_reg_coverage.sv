`timescale 1ns/1ps
module shift_reg_coverage (
  input logic       clk,
  input logic       rst_n,
  input logic       load,
  input logic       shift_en,
  input logic       din,
  input logic [7:0] parallel_in,
  input logic [7:0] dout,
  input logic       serial_out
);

  covergroup shift_reg_coverage_cg @(posedge clk);
    option.per_instance = 1;

    // Cover `rst_n` being asserted (0) or deasserted (1).
    rst_n_cp : coverpoint rst_n {
      bins asserted   = {0};
      bins deasserted = {1};
    }

    // Cover `load` control signal.
    load_cp : coverpoint load {
      bins active   = {1};
      bins inactive = {0};
    }

    // Cover `shift_en` control signal.
    shift_en_cp : coverpoint shift_en {
      bins active   = {1};
      bins inactive = {0};
    }

    // Cover `din` (serial input) values.
    din_cp : coverpoint din {
      bins zero = {0};
      bins one  = {1};
    }

    // Cover `parallel_in` values.
    // RTL shows `parallel_in` can be any 8-bit value.
    parallel_in_cp : coverpoint parallel_in {
      bins all_zero  = {8'h00};
      bins all_one   = {8'hFF};
      bins mid_range = {[8'h01:8'hFE]};
    }

    // Cover `dout` (register output) values.
    // RTL shows `dout` can be 8'h00 on reset, or `parallel_in`, or shifted values.
    dout_cp : coverpoint dout {
      bins all_zero = {8'h00};
      bins all_one  = {8'hFF};
      bins other    = default;
    }

    // Cover `serial_out` (MSB of register) values.
    serial_out_cp : coverpoint serial_out {
      bins zero = {0};
      bins one  = {1};
    }

    // Cross `load` and `shift_en` to cover control signal interactions.
    // This covers:
    // - Register being parallel loaded (load=1, shift_en=0)
    // - Register shifting (load=0, shift_en=1)
    // - Load takes priority (load=1, shift_en=1)
    // - Register holds (load=0, shift_en=0)
    load_x_shift_en_x : cross load_cp, shift_en_cp;

    // Cross `shift_en` and `din` to cover shifting in a one and a zero.
    // Ignore bins where `shift_en` is inactive, as `din` has no effect on shifting then.
    shift_en_x_din_x : cross shift_en_cp, din_cp {
      ignore_bins no_shift = binsof(shift_en_cp.inactive);
    }

    // Cross `rst_n` and `shift_en` to cover reset asserted while a shift is in progress.
    rst_n_x_shift_en_x : cross rst_n_cp, shift_en_cp;

    // Cross `din` and `serial_out` to cover the input/output activity during shifts.
    // This helps cover a bit being shifted through the register, by observing
    // the input and the final output bit when shifting is enabled.
    // FIX: The `iff` condition for a cross must be part of the cross declaration itself,
    // not inside the cross's body (i.e., not within the curly braces `{}`).
    din_x_serial_out_x : cross din_cp, serial_out_cp iff (shift_en);

  endgroup

  shift_reg_coverage_cg cg_inst = new();

  // Report the covergroup score directly from the simulator, so the
  // number does not depend on the coverage database or IMC's flags.
  final begin
    $display("SV_FUNCTIONAL_COVERAGE: %0.4f", $get_coverage());
    $display("SV_CG_INST_COVERAGE: %0.4f", cg_inst.get_inst_coverage());
  end

endmodule