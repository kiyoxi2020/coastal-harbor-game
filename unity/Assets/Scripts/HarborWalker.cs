using UnityEngine;

namespace CoastalHarbor
{
    [RequireComponent(typeof(CharacterController))]
    public sealed class HarborWalker : MonoBehaviour
    {
        public Transform View;
        public Transform Visual;
        public Vector3 Spawn;
        public bool Automated;
        public float WalkSpeed = HarborLocomotion.WalkMetersPerSecond;
        public float RunSpeed = HarborLocomotion.RunMetersPerSecond;
        public HarborLocomotion Locomotion;
        public float ActualPlanarSpeed { get; private set; }
        private CharacterController controller;
        private float verticalSpeed;

        public static Vector3 CameraRelative(Vector2 input, Vector3 forward)
        {
            forward.y = 0;
            if (forward.sqrMagnitude < 0.001f) forward = Vector3.forward;
            forward.Normalize();
            Vector3 right = Vector3.Cross(Vector3.up, forward);
            return Vector3.ClampMagnitude(right * input.x + forward * input.y, 1);
        }

        private void Awake()
        {
            controller = GetComponent<CharacterController>();
        }

        private void Update()
        {
            if (transform.position.y < -3) ResetPosition();
            if (Automated) return;
            if (Input.GetKeyDown(KeyCode.R)) ResetPosition();
            Vector2 input = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
            Drive(CameraRelative(input, View.forward), Input.GetKey(KeyCode.LeftShift), Time.deltaTime);
        }

        public void Drive(Vector3 direction, bool running, float seconds)
        {
            if (seconds <= 0 || float.IsNaN(seconds) || float.IsInfinity(seconds))
            {
                ActualPlanarSpeed = 0;
                if (Locomotion != null) Locomotion.SetSpeed(0, 0);
                return;
            }
            if (controller == null) controller = GetComponent<CharacterController>();
            direction.y = 0;
            direction = Vector3.ClampMagnitude(direction, 1);
            if (controller.isGrounded && verticalSpeed < 0) verticalSpeed = -2;
            verticalSpeed = Mathf.Max(verticalSpeed - 20 * seconds, -25);
            Vector3 before = transform.position;
            controller.Move((direction * (running ? RunSpeed : WalkSpeed) + Vector3.up * verticalSpeed) * seconds);
            Vector3 displacement = transform.position - before;
            displacement.y = 0;
            ActualPlanarSpeed = displacement.magnitude / seconds;
            if (Locomotion != null) Locomotion.SetSpeed(ActualPlanarSpeed, seconds);
            if (direction.sqrMagnitude > 0.01f && Visual != null)
                Visual.rotation = Quaternion.Slerp(Visual.rotation, Quaternion.LookRotation(direction), 1 - Mathf.Exp(-14 * seconds));
        }

        public void Teleport(Vector3 position)
        {
            if (controller == null) controller = GetComponent<CharacterController>();
            controller.enabled = false;
            transform.position = position;
            controller.enabled = true;
            verticalSpeed = 0;
            ActualPlanarSpeed = 0;
            if (Locomotion != null) Locomotion.SetSpeed(0, 0);
        }

        public void ResetPosition()
        {
            Teleport(Spawn);
        }
    }
}
