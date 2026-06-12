// --------------------------------------------------
// imu_degree_publisher.cpp
// Subscribe to /imu (sensor_msgs/Imu) dengan orientasi quaternion,
// konversi ke Roll/Pitch/Yaw dalam DERAJAT, lalu publish ke /imu_degrees
// Tujuan: robustness check / debugging
// --------------------------------------------------

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <geometry_msgs/msg/vector3_stamped.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2/LinearMath/Matrix3x3.h>
#include <cmath>

#define RAD_TO_DEG (180.0 / M_PI)

class ImuDegreePublisher : public rclcpp::Node
{
public:
  ImuDegreePublisher()
  : Node("imu_degree_publisher")
  {
    // Parameter: topik input dan output bisa dikonfigurasi
    this->declare_parameter("imu_input_topic",  "/imu");
    this->declare_parameter("imu_output_topic", "/imu_degrees");
    this->declare_parameter("print_to_console",  true);

    std::string input_topic  = this->get_parameter("imu_input_topic").as_string();
    std::string output_topic = this->get_parameter("imu_output_topic").as_string();
    print_to_console_        = this->get_parameter("print_to_console").as_bool();

    // Subscriber ke topik IMU asli
    imu_sub_ = this->create_subscription<sensor_msgs::msg::Imu>(
      input_topic, 10,
      std::bind(&ImuDegreePublisher::imu_callback, this, std::placeholders::_1));

    // Publisher RPY dalam derajat menggunakan Vector3Stamped
    // x = Roll (deg), y = Pitch (deg), z = Yaw (deg)
    rpy_pub_ = this->create_publisher<geometry_msgs::msg::Vector3Stamped>(output_topic, 10);

    RCLCPP_INFO(this->get_logger(),
      "imu_degree_publisher aktif\n  Mendengarkan : %s\n  Publish ke   : %s (x=Roll, y=Pitch, z=Yaw, satuan DERAJAT)",
      input_topic.c_str(), output_topic.c_str());
  }

private:
  bool print_to_console_;
  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
  rclcpp::Publisher<geometry_msgs::msg::Vector3Stamped>::SharedPtr rpy_pub_;

  void imu_callback(const sensor_msgs::msg::Imu::SharedPtr msg)
  {
    // ── Quaternion → RPY (radian) ──────────────────────────────────────────
    tf2::Quaternion q(
      msg->orientation.x,
      msg->orientation.y,
      msg->orientation.z,
      msg->orientation.w);

    double roll_rad, pitch_rad, yaw_rad;
    tf2::Matrix3x3(q).getRPY(roll_rad, pitch_rad, yaw_rad);

    // ── Konversi ke derajat ────────────────────────────────────────────────
    double roll_deg  = roll_rad  * RAD_TO_DEG;
    double pitch_deg = pitch_rad * RAD_TO_DEG;
    double yaw_deg   = yaw_rad   * RAD_TO_DEG;

    // ── Angular velocity (rad/s) → deg/s ──────────────────────────────────
    double gx_deg = msg->angular_velocity.x * RAD_TO_DEG;
    double gy_deg = msg->angular_velocity.y * RAD_TO_DEG;
    double gz_deg = msg->angular_velocity.z * RAD_TO_DEG;

    // ── Publish RPY (deg) ──────────────────────────────────────────────────
    geometry_msgs::msg::Vector3Stamped rpy_msg;
    rpy_msg.header        = msg->header;
    rpy_msg.vector.x      = roll_deg;   // Roll  [deg]
    rpy_msg.vector.y      = pitch_deg;  // Pitch [deg]
    rpy_msg.vector.z      = yaw_deg;    // Yaw   [deg]
    rpy_pub_->publish(rpy_msg);

    // ── Console print (opsional, bisa di-disable via parameter) ───────────
    if (print_to_console_)
    {
      RCLCPP_INFO(this->get_logger(),
        "\n"
        "  ┌─────────────────────────────────────────────┐\n"
        "  │  ORIENTASI (derajat)                         │\n"
        "  │   Roll  : %+9.3f °                          │\n"
        "  │   Pitch : %+9.3f °                          │\n"
        "  │   Yaw   : %+9.3f °                          │\n"
        "  ├─────────────────────────────────────────────┤\n"
        "  │  GYRO (deg/s)                                │\n"
        "  │   Gx    : %+9.3f °/s                        │\n"
        "  │   Gy    : %+9.3f °/s                        │\n"
        "  │   Gz    : %+9.3f °/s                        │\n"
        "  ├─────────────────────────────────────────────┤\n"
        "  │  AKSELERASI (m/s²)                           │\n"
        "  │   Ax    : %+9.3f                            │\n"
        "  │   Ay    : %+9.3f                            │\n"
        "  │   Az    : %+9.3f                            │\n"
        "  └─────────────────────────────────────────────┘",
        roll_deg, pitch_deg, yaw_deg,
        gx_deg, gy_deg, gz_deg,
        msg->linear_acceleration.x,
        msg->linear_acceleration.y,
        msg->linear_acceleration.z);
    }
  }
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<ImuDegreePublisher>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}