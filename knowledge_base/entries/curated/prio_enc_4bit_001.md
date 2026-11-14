---
id: "prio_enc_4bit_001"
context.module: "PRIO_ENC"
context.data_width: 4
context.type: "4-bit priority encoder"
signals: ["d", "y"]
verified: true
provenance: "curated_seed"
category: "curated"
---

## Requirement
Cover 4-bit priority encoder behavior for all priority levels of input d and corresponding encoded output y, including cross coverage of legal input-output combinations.

## Notes
(none)

## RTL
```verilog
module prio_enc(d, y);
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
endmodule
```

## Coverage model
```systemverilog
covergroup cg_pe (ref logic [3:0] d, ref logic [1:0] y);

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

endgroup
```
