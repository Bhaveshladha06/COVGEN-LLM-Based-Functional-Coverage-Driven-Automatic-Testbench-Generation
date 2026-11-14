---
id: "bin2gray_4bit_001"
context.module: "BIN2GRAY"
context.data_width: 4
context.type: "4-bit binary to Gray converter"
signals: ["bin", "gray"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover 4-bit binary-to-Gray conversion across the full input range including the zero and maximum values, and confirm every Gray output code is produced.

## Notes
(none)

## RTL
```verilog
module bin2gray(bin, gray);
  input [3:0] bin;
  output [3:0] gray;
  assign gray = bin ^ (bin >> 1);
endmodule
```

## Coverage model
```systemverilog
covergroup cg_b2g (ref logic [3:0] bin, gray);
  bin_cp : coverpoint bin {
    bins value[] = {[0:15]};
  }
  gray_cp : coverpoint gray {
    bins code[] = {[0:15]};
  }
endgroup
```
