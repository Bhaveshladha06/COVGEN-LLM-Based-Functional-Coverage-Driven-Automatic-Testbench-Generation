---
id: "seven_seg_4bit_001"
context.module: "SEVEN_SEG"
context.data_width: 4
context.type: "seven-segment decoder"
signals: ["bcd", "seg"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover the seven-segment decoder for all ten decimal digit inputs, the blanked output for invalid inputs, and confirm each distinct segment pattern is produced.

## Notes
(none)

## RTL
```verilog
module seven_seg(bcd, seg);
  input [3:0] bcd;
  output reg [6:0] seg;
  always @(*) begin
    case (bcd)
      4'd0: seg = 7'b1111110;
      4'd1: seg = 7'b0110000;
      4'd2: seg = 7'b1101101;
      4'd3: seg = 7'b1111001;
      4'd4: seg = 7'b0110011;
      4'd5: seg = 7'b1011011;
      4'd6: seg = 7'b1011111;
      4'd7: seg = 7'b1110000;
      4'd8: seg = 7'b1111111;
      4'd9: seg = 7'b1111011;
      default: seg = 7'b0000000;
    endcase
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_7seg (ref logic [3:0] bcd, ref logic [6:0] seg);
  bcd_cp : coverpoint bcd {
    bins digit[]  = {[0:9]};
    bins invalid  = {[10:15]};
  }
  seg_cp : coverpoint seg {
    bins blank = {7'b0000000};
    bins lit   = {[7'b0000001:7'b1111111]};
  }
  bcd_x_seg : cross bcd_cp, seg_cp;
endgroup
```
