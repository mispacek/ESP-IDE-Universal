# madgwick.py  —  minimal-overhead Madgwick AHRS pro MicroPython
# MIT Licence, port z https://x-io.co.uk
from math import sqrt, atan2, asin

class Madgwick:
    def __init__(self, beta=0.1):
        self.beta = beta          # 2*proporční zisk
        self.reset()

    # ========================================================
    def reset(self):
        self.q0, self.q1, self.q2, self.q3 = 1.0, 0.0, 0.0, 0.0
        self.sample_period = 0.01  # pro začátek 100 Hz

    # ========================================================
    def update_imu(self, gx, gy, gz, ax, ay, az, dt):
        """gx,gy,gz [rad/s],  ax,ay,az [g],  dt [s]"""
        self.sample_period = dt

        # normalizuj akcelerometr
        norm = sqrt(ax*ax + ay*ay + az*az)
        if norm == 0:
            return                      # nelze normalizovat
        ax /= norm; ay /= norm; az /= norm

        q0, q1, q2, q3 = self.q0, self.q1, self.q2, self.q3

        # pomocné proměnné (zrychluje výpočet)
        _2q0 = 2.0 * q0
        _2q1 = 2.0 * q1
        _2q2 = 2.0 * q2
        _2q3 = 2.0 * q3
        _4q0 = 4.0 * q0
        _4q1 = 4.0 * q1
        _4q2 = 4.0 * q2
        _8q1 = 8.0 * q1
        _8q2 = 8.0 * q2
        q0q0 = q0 * q0
        q1q1 = q1 * q1
        q2q2 = q2 * q2
        q3q3 = q3 * q3

        # nabla f × J^T (Madgwick rovnice (33))
        s0 = _4q0 * q2q2 + _2q2 * ax + _4q0 * q1q1 - _2q1 * ay
        s1 = _4q1 * q3q3 - _2q3 * ax + 4.0 * q0q0 * q1 - _2q0 * ay - _4q1 + _8q1 * q1q1 + _8q1 * q2q2 + _4q1 * az
        s2 = 4.0 * q0q0 * q2 + _2q0 * ax + _4q2 * q3q3 - _2q3 * ay - _4q2 + _8q2 * q1q1 + _8q2 * q2q2 + _4q2 * az
        s3 = 4.0 * q1q1 * q3 - _2q1 * ax + 4.0 * q2q2 * q3 - _2q2 * ay
        norm = sqrt(s0*s0 + s1*s1 + s2*s2 + s3*s3)
        if norm == 0:
            return
        s0 /= norm; s1 /= norm; s2 /= norm; s3 /= norm

        # kvaternionová derivace – omega
        qDot0 = 0.5 * (-q1 * gx - q2 * gy - q3 * gz) - self.beta * s0
        qDot1 = 0.5 * ( q0 * gx + q2 * gz - q3 * gy) - self.beta * s1
        qDot2 = 0.5 * ( q0 * gy - q1 * gz + q3 * gx) - self.beta * s2
        qDot3 = 0.5 * ( q0 * gz + q1 * gy - q2 * gx) - self.beta * s3

        # integruj kvaternion
        q0 += qDot0 * dt
        q1 += qDot1 * dt
        q2 += qDot2 * dt
        q3 += qDot3 * dt
        norm = sqrt(q0*q0 + q1*q1 + q2*q2 + q3*q3)
        self.q0, self.q1, self.q2, self.q3 = q0/norm, q1/norm, q2/norm, q3/norm

    # ========================================================
    def yaw_pitch_roll(self):
        """Vrací (roll, pitch, yaw) v radiánech."""
        q0, q1, q2, q3 = self.q0, self.q1, self.q2, self.q3
        roll  = atan2(2*(q0*q1 + q2*q3), 1 - 2*(q1*q1 + q2*q2))
        pitch = asin (max(-1, min(1, 2*(q0*q2 - q3*q1))))
        yaw   = atan2(2*(q0*q3 + q1*q2), 1 - 2*(q2*q2 + q3*q3))
        return roll, pitch, yaw
