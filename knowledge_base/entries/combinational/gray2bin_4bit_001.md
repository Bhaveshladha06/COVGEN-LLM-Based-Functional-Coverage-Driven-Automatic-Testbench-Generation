---
id: "gray2bin_4bit_001"
context.module: "GRAY2BIN"
context.data_width: 4
context.type: "4-bit Gray to binary converter"
signals: ["gray", "bin"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover 4-bit Gray-to-binary conversion for every Gray input code and confirm the full range of binary outputs is produced.

## Notes
(none)

## RTL
```verilog
module gray2bin(gray, bin);
  input [3:0] gray;
  output [3:0] bin;
  assign bin[3] = gray[3];
  assign bin[2] = gray[3] ^ gray[2];
  assign bin[1] = gray[3] ^ gray[2] ^ gray[1];
  assign bin[0] = gray[3] ^ gray[2] ^ gray[1] ^ gray[0];
endmodule
```

## Coverage model
```systemverilog
covergroup cg_g2b (ref logic [3:0] gray, bin);
  gray_cp : coverpoint gray {
    bins code[] = {[0:15]};
  }
  bin_cp : coverpoint bin {
    bins value[] = {[0:15]};
  }
endgroup
```
