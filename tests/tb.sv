/**
 * File              : tb.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 06.08.2024
 * Last Modified Date: 06.08.2024
 */
module tb
#(
  parameter int REG_OUTPUT = 1,
  parameter int DATA_WIDTH = 32
)(
  input                           clk,
  input                           rst,
  // Input I/F
  input                           in_valid_i,
  output  logic                   in_ready_o,
  input   logic [DATA_WIDTH-1:0]  in_data_i,

  // Output I/F
  output  logic                   out_valid_o,
  input                           out_ready_i,
  output  logic [DATA_WIDTH-1:0]  out_data_o
);
  typedef logic [DATA_WIDTH-1:0] data_t;

  skid_buffer #(
    .REG_OUTPUT   (REG_OUTPUT),
    .type_t       (data_t)
  ) u_skid_buffer (
    .clk          (clk),
    .rst          (rst),
    // Input I/F
    .in_valid_i   (in_valid_i),
    .in_ready_o   (in_ready_o),
    .in_data_i    (in_data_i),

    // Output I/F
    .out_valid_o  (out_valid_o),
    .out_ready_i  (out_ready_i),
    .out_data_o   (out_data_o)
  );
endmodule
