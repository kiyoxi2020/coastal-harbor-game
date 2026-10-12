using UnityEngine;

namespace CoastalHarbor
{
    public sealed class HarborCamera : MonoBehaviour
    {
        public Transform Target;
        public Vector3 OverviewPosition;
        public Vector3 OverviewFocus;
        public Vector3 InitialOffset = new Vector3(8, 10, -10);
        public bool Overview;
        public float Distance = 11;
        private float yaw;
        private float pitch = 44;

        private void Start()
        {
            yaw = Mathf.Atan2(InitialOffset.x, InitialOffset.z) * Mathf.Rad2Deg;
            if (!Overview) Snap();
        }

        private void LateUpdate()
        {
            if (Input.GetKeyDown(KeyCode.Tab)) Overview = !Overview;
            if (Input.GetMouseButton(1) && !Overview)
            {
                yaw += Input.GetAxis("Mouse X") * 3;
                pitch = Mathf.Clamp(pitch - Input.GetAxis("Mouse Y") * 2, 25, 65);
            }
            Distance = Mathf.Clamp(Distance - Input.mouseScrollDelta.y, 6, 18);
            Vector3 focus = Overview ? OverviewFocus : Target.position + Vector3.up * 0.8f;
            Vector3 desired = Overview ? OverviewPosition : FollowPosition(focus);
            transform.position = Vector3.Lerp(transform.position, desired, 1 - Mathf.Exp(-9 * Time.deltaTime));
            transform.LookAt(focus);
        }

        private Vector3 FollowPosition(Vector3 focus)
        {
            Vector3 offset = Quaternion.Euler(0, yaw, 0) * new Vector3(0, Mathf.Sin(pitch * Mathf.Deg2Rad), Mathf.Cos(pitch * Mathf.Deg2Rad)) * Distance;
            if (Physics.SphereCast(focus, 0.2f, offset.normalized, out RaycastHit hit, offset.magnitude, 1 << 8))
                return focus + offset.normalized * Mathf.Max(0.5f, hit.distance - 0.1f);
            return focus + offset;
        }

        public void Snap()
        {
            Vector3 focus = Overview ? OverviewFocus : Target.position + Vector3.up * 0.8f;
            transform.position = Overview ? OverviewPosition : FollowPosition(focus);
            transform.LookAt(focus);
        }
    }
}
