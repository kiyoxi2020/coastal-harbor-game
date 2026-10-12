using UnityEngine;

namespace CoastalHarbor
{
    public sealed class HarborPoint : MonoBehaviour
    {
        public string Title;
        [TextArea] public string Description;
        public float Radius = 2;

        public bool InReach(Vector3 position)
        {
            Vector3 distance = transform.position - position;
            distance.y = 0;
            return distance.sqrMagnitude <= Radius * Radius;
        }
    }
}
