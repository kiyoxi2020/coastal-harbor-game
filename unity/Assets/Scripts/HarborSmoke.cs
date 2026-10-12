using System;
using System.Collections;
using System.IO;
using UnityEngine;

namespace CoastalHarbor
{
    public sealed class HarborSmoke : MonoBehaviour
    {
        public HarborWalker Player;
        public HarborCamera View;
        public Vector3 WallStart;
        public Vector3 WallDirection;
        public Vector3 DockStart;
        public Vector3 DockDirection;
        public float WallDistanceToFace = 2;

        private IEnumerator Start()
        {
            string[] arguments = Environment.GetCommandLineArgs();
            int outputIndex = Array.IndexOf(arguments, "--harbor-smoke");
            if (outputIndex < 0) yield break;
            string output = arguments[outputIndex + 1];
            Directory.CreateDirectory(output);
            Player.Automated = true;
            for (int frame = 0; frame < 30; frame++) { Player.Drive(Vector3.zero, false, 1f / 60); yield return null; }
            Vector3 start = Player.transform.position;
            Vector3 route = -WallDirection;
            for (int frame = 0; frame < 30; frame++) { Player.Drive(route, false, 1f / 60); yield return null; }
            bool moved = Vector3.Distance(start, Player.transform.position) > 0.6f;
            Player.Teleport(WallStart);
            for (int frame = 0; frame < 90; frame++) { Player.Drive(WallDirection, false, 1f / 60); yield return null; }
            float wallTravel = Vector3.Dot(Player.transform.position - WallStart, WallDirection);
            CharacterController capsule = Player.GetComponent<CharacterController>();
            float contactLimit = WallDistanceToFace - capsule.radius + capsule.skinWidth * 2;
            Vector3 contact = Player.transform.position;
            for (int frame = 0; frame < 30; frame++) { Player.Drive(WallDirection, false, 1f / 60); yield return null; }
            bool blocked = wallTravel > 0.1f && wallTravel <= contactLimit && Vector3.Distance(contact, Player.transform.position) < 0.01f;
            Player.Teleport(DockStart);
            for (int frame = 0; frame < 110; frame++) { Player.Drive(DockDirection, false, 1f / 60); yield return null; }
            bool dock = Player.transform.position.y > 0.5f && Vector3.Dot(Player.transform.position - DockStart, DockDirection) > 2.0f;
            Player.Teleport(new Vector3(0, -8, 0));
            yield return null;
            yield return null;
            bool reset = Vector3.Distance(Player.transform.position, Player.Spawn) < 0.15f;
            Player.ResetPosition();
            View.Overview = true;
            View.Snap();
            for (int frame = 0; frame < 20; frame++) yield return null;
            yield return new WaitForEndOfFrame();
            ScreenCapture.CaptureScreenshot(Path.Combine(output, "unity-day.png"));
            for (int frame = 0; frame < 10; frame++) yield return null;
            FindFirstObjectByType<HarborExperience>().SetEvening(true);
            for (int frame = 0; frame < 20; frame++) yield return null;
            yield return new WaitForEndOfFrame();
            ScreenCapture.CaptureScreenshot(Path.Combine(output, "unity-dusk.png"));
            for (int frame = 0; frame < 10; frame++) yield return null;
            bool success = moved && blocked && dock && reset;
            File.WriteAllText(Path.Combine(output, "smoke-result.json"),
                "{\"movement\":" + moved.ToString().ToLowerInvariant() +
                ",\"wallCollision\":" + blocked.ToString().ToLowerInvariant() +
                ",\"dockTraversal\":" + dock.ToString().ToLowerInvariant() +
                ",\"fallRecovery\":" + reset.ToString().ToLowerInvariant() + "}");
            Debug.Log("HARBOR_SMOKE " + success + " wallTravel=" + wallTravel);
            Application.Quit(success ? 0 : 1);
        }
    }
}
