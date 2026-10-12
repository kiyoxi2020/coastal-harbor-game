using UnityEngine;

namespace CoastalHarbor
{
    public sealed class HarborLocomotion : MonoBehaviour
    {
        public const float WalkMetersPerSecond = 1.35f;
        public const float RunMetersPerSecond = 2.8f;
        public Animator Animator;
        private static readonly int SpeedId = UnityEngine.Animator.StringToHash("Speed");

        public void SetSpeed(float measuredSpeed, float seconds)
        {
            if (Animator == null) return;
            float speed = float.IsNaN(measuredSpeed) || float.IsInfinity(measuredSpeed)
                ? 0 : Mathf.Clamp(measuredSpeed, 0, RunMetersPerSecond);
            if (speed < 0.05f || seconds <= 0) Animator.SetFloat(SpeedId, 0);
            else Animator.SetFloat(SpeedId, speed, 0.08f, seconds);
        }
    }
}
