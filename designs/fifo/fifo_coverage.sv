`timescale 1ns/1ps
module fifo_coverage (
  input logic       clk,
  input logic       rst_n,
  input logic       wr_en,
  input logic       rd_en,
  input logic [7:0] din,
  input logic [7:0] dout,
  input logic       full,
  input logic       empty,
  input logic [3:0] count
);

  covergroup fifo_coverage_cg @(posedge clk);
    option.per_instance = 1;

    // RTL analysis for 'count':
    // The 'count' signal is declared [3:0], but the FIFO depth is 8.
    // The 'full' flag is asserted when count == 4'd8.
    // The 'empty' flag is asserted when count == 4'd0.
    // The 'count' value is reset to 0, increments by 1 (max 8), and decrements by 1 (min 0).
    // Therefore, 'count' will only ever range from 0 to 8. Values 9-15 are unreachable.
    count_cp : coverpoint count {
      bins empty_c    = {0};
      bins almost_e   = {1};
      bins mid_range  = {[2:7]}; // Occupancy levels between almost empty and full
      bins full_c     = {8};
      illegal_bins overflow = {[9:15]}; // Values 9-15 are unreachable for a FIFO of depth 8
      bins not_empty_c = {[1:8]}; // Helper bin for crosses, represents count > 0
    }

    // RTL analysis for 'wr_en': Single bit input.
    wr_en_cp : coverpoint wr_en {
      bins idle_wr  = {0};
      bins write_en = {1};
    }

    // RTL analysis for 'rd_en': Single bit input.
    rd_en_cp : coverpoint rd_en {
      bins idle_rd = {0};
      bins read_en = {1};
    }

    // RTL analysis for 'din': 8-bit input.
    // Requirement: "Cover the data input at its minimum, maximum and mid-range values"
    din_cp : coverpoint din {
      bins min_val = {8'h00};
      bins mid_val = {[8'h01:8'hFE]};
      bins max_val = {8'hFF};
    }

    // RTL analysis for 'rst_n': Active low reset.
    rst_n_cp : coverpoint rst_n {
      bins active_rst   = {0};
      bins inactive_rst = {1};
    }

    // RTL analysis for 'full': Output flag, derived from count.
    full_cp : coverpoint full {
      bins not_full_flag = {0};
      bins is_full_flag  = {1};
    }

    // RTL analysis for 'empty': Output flag, derived from count.
    empty_cp : coverpoint empty {
      bins not_empty_flag = {0};
      bins is_empty_flag  = {1};
    }

    // Requirement: "Cover a simultaneous read and write while the FIFO is partially filled,
    // so the occupancy stays unchanged."
    // This is a transition where count goes from X to X, under specific conditions.
    // Transition bins must use constants or constant ranges and cannot be part of a cross.
    // The original error was using a bin name 'mid_range' in a transition bin, which is not allowed.
    count_hold_t_cp : coverpoint count iff (wr_en && !full && rd_en && !empty) {
      bins hold_mid = ([2:7] => [2:7]); // Corrected: use constant range instead of bin name
    }

    // Requirement: "Cover a write attempted while the FIFO is full"
    wr_en_full_x : cross wr_en_cp, full_cp {
      bins write_when_full = binsof(wr_en_cp.write_en) && binsof(full_cp.is_full_flag);
    }

    // Requirement: "Cover a read attempted while it is empty"
    rd_en_empty_x : cross rd_en_cp, empty_cp {
      bins read_when_empty = binsof(rd_en_cp.read_en) && binsof(empty_cp.is_empty_flag);
    }

    // Requirement: "Cover the cross of the write enable against the read enable"
    wr_rd_x : cross wr_en_cp, rd_en_cp;

    // Requirement: "and the cross of each enable against the full and empty flags."
    // wr_en_full_x already covers wr_en vs full.
    wr_en_empty_x : cross wr_en_cp, empty_cp;
    rd_en_full_x  : cross rd_en_cp, full_cp;
    // rd_en_empty_x already covers rd_en vs empty.

    // Requirement: "Cover the reset asserted while the FIFO holds data."
    // When rst_n is active (0) at posedge clk, 'count' is sampled *before* the non-blocking update.
    // Therefore, 'count' can be non-zero at the sampling instant if the FIFO held data prior to reset.
    rst_n_data_x : cross rst_n_cp, count_cp {
      bins reset_with_data = binsof(rst_n_cp.active_rst) && binsof(count_cp.not_empty_c);
    }

  endgroup

  fifo_coverage_cg cg_inst = new();

  // Report the covergroup score directly from the simulator, so the
  // number does not depend on the coverage database or IMC's flags.
  final begin
    $display("SV_FUNCTIONAL_COVERAGE: %0.4f", $get_coverage());
    $display("SV_CG_INST_COVERAGE: %0.4f", cg_inst.get_inst_coverage());
  end
endmodule