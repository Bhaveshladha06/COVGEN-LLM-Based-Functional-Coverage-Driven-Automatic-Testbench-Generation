// 4-bit ALU. Tests OPCODE x OPERAND crosses and illegal/unused opcodes.
module alu4 (a, b, opcode, result, zero, carry);
    input      [3:0] a;
    input      [3:0] b;
    input      [2:0] opcode;
    output reg [3:0] result;
    output           zero;
    output reg       carry;

    always @(*) begin
        carry = 1'b0;
        case (opcode)
            3'd0: {carry, result} = a + b;
            3'd1: {carry, result} = a - b;
            3'd2: result = a & b;
            3'd3: result = a | b;
            3'd4: result = a ^ b;
            3'd5: result = ~a;
            3'd6: result = a << 1;
            3'd7: result = a >> 1;
            default: result = 4'd0;
        endcase
    end

    assign zero = (result == 4'd0);
endmodule
