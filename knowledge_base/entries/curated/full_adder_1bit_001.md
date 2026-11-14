---
id: "full_adder_1bit_001"
context.module: "FULL_ADDER"
context.data_width: 1
context.type: "1-bit full adder"
signals: ["a", "b", "cin", "sum", "cout"]
verified: true
provenance: "curated_seed"
category: "curated"
---

## Requirement
Cover full adder behavior for all combinations of inputs a, b, cin and resulting sum, cout outputs.

## Notes
(none)

## RTL
```verilog
module full_adder(a, b, cin, sum, cout);
  input a, b, cin;
  output sum, cout;

  assign {cout, sum} = a + b + cin;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_fa (ref logic a, b, cin, sum, cout);

  // Input combinations
  cp_inputs: coverpoint {a,b,cin};

  // Output coverage
  cp_sum:  coverpoint sum;
  cp_cout: coverpoint cout;

  // Cross to relate inputs & outputs
  cp_in_out: cross cp_inputs, cp_sum, cp_cout;

endgroup
```
