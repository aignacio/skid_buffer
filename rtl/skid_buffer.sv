/**
 * File              : skid_buffer.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 02.06.2024
 * Last Modified Date: 06.08.2024
 * Description       : Skid Buffer to break combo path between pip flops
 */
module skid_buffer
#(
  parameter int REG_OUTPUT = 1,
  parameter type type_t    = logic
)(
  input           clk,
  input           rst,
  // Input I/F
  input           in_valid_i,
  output  logic   in_ready_o,
  input   type_t  in_data_i,

  // Output I/F
  output  logic   out_valid_o,
  input           out_ready_i,
  output  type_t  out_data_o
);

  logic     valid_ff, next_valid; // Only used in case REG_OUTPUT == 1
  logic     ready_ff, next_ready;
  type_t    buff_ff, next_buff;
  type_t    data_out_ff, next_data_out; // Only used in case REG_OUTPUT == 1

  always_comb begin : ready_logic
    in_ready_o = ready_ff;
    next_ready = ready_ff;

    if ((in_valid_i && in_ready_o) && (out_valid_o && ~out_ready_i)) begin
      next_ready = 1'b0;
    end
    else if (out_ready_i) begin
        next_ready = 1'b1;
    end
  end : ready_logic

  always_comb begin : valid_data_logic
    next_valid = valid_ff;
    next_buff = buff_ff;
    next_data_out = data_out_ff;


    if (REG_OUTPUT == 0) begin : REG_OUTPUT_FALSE
      if (ready_ff == 1'b0) begin
        out_valid_o = 1'b1;
        out_data_o = buff_ff;
      end
      else begin
        out_valid_o = in_valid_i;

        if (in_valid_i) begin
          next_buff = in_data_i;
          out_data_o = in_data_i;
        end
        else begin
          out_data_o = '0;
        end
      end
    end : REG_OUTPUT_FALSE
    else begin : REG_OUTPUT_TRUE
      out_data_o = data_out_ff;
      out_valid_o = valid_ff;

      if ((in_valid_i && in_ready_o) && (out_valid_o && ~out_ready_i)) begin
        next_buff = in_data_i;
      end

      if (~valid_ff) begin
        next_valid = in_valid_i;
        next_data_out = in_valid_i ? in_data_i : type_t'('0);
      end
      else begin
        if (out_ready_i && ~in_valid_i && ready_ff) begin
          // If slave is available + have no new req + nothing buff:
          // valid == 0
          // data_out == 0
          next_data_out = type_t'('0);
          next_valid = 1'b0;
        end
        else if (out_ready_i && ~ready_ff) begin
          // If slave is available + data buff:
          // valid == 1
          // data_out == buff
          next_data_out = buff_ff;
        end
        else if (out_ready_i && in_valid_i && ready_ff) begin
          // If slave is available + have new req + nothing buff:
          // valid == 1
          // data_out == data_in
          next_data_out = in_data_i;
        end
      end
    end : REG_OUTPUT_TRUE
  end : valid_data_logic

  always_ff @ (posedge clk or posedge rst) begin
    if (rst) begin
      ready_ff    <= 1'b1;
      valid_ff    <= 1'b0;
      buff_ff     <= type_t'('0);
      data_out_ff <= type_t'('0);
    end
    else begin
      ready_ff    <= next_ready;
      valid_ff    <= next_valid;
      buff_ff     <= next_buff;
      data_out_ff <= next_data_out;
    end
  end
endmodule
