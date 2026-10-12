using System;
using System.Collections;
using System.IO;
using System.Linq;
using UnityEngine;

namespace CoastalHarbor
{
    public sealed class HarborCharacterSmoke : MonoBehaviour
    {
        public HarborWalker Player;
        public HarborCamera View;
        public HarborSmoke Route;
        private string output;
        private string phase;
        private int frameIndex;
        private bool active;
        private Transform shin;
        private Quaternion firstShin;
        private float shinMotion;
        private HarborExperience experience;
        private GUIStyle caption;

        [Serializable] private sealed class Result
        {
            public bool idle, walk, run, turn, wallStopsAnimation, dock, fallRecovery, groundContact, passed;
            public float walkDistance, runDistance, walkBoneDegrees, runBoneDegrees, blockedSpeed, footGap;
            public int capturedFrames;
            public string scope = "macOS standalone, automated movement, actual Unity rendered frames";
        }

        private IEnumerator Start()
        {
            string[] arguments = Environment.GetCommandLineArgs();
            int index = Array.IndexOf(arguments, "--character-smoke");
            if (index < 0) yield break;
            if (index + 1 >= arguments.Length) throw new ArgumentException("Missing character validation output directory");
            output = arguments[index + 1];
            Directory.CreateDirectory(Path.Combine(output, "frames"));
            active = true;
            Application.runInBackground = true;
            Time.captureFramerate = 30;
            Player.Automated = true;
            View.enabled = false;
            experience = FindFirstObjectByType<HarborExperience>();
            experience.enabled = false;
            shin = Player.Visual.GetComponentsInChildren<Transform>().Single(t => t.name == "Shin.L");
            Result result = new Result();
            Player.Teleport(new Vector3(2, 0.95f, 2.3f));
            Player.Visual.rotation = Quaternion.LookRotation(Vector3.left);
            phase = "待机";
            yield return Steps(Vector3.zero, false, 30, false);
            yield return Steps(Vector3.zero, false, 45, true);
            result.idle = ClipIs("Idle");
            result.footGap = FootGap();
            result.groundContact = result.footGap > -0.06f && result.footGap < 0.08f;
            Capture("character-idle.png");

            phase = "行走";
            Vector3 start = Player.transform.position;
            firstShin = shin.localRotation;
            shinMotion = 0;
            yield return Steps(Vector3.left, false, 60, true);
            result.walkDistance = PlanarDistance(start, Player.transform.position);
            result.walkBoneDegrees = shinMotion;
            result.walk = result.walkDistance > 2 && shinMotion > 5 && ClipIs("Walk");
            Capture("character-walk.png");

            phase = "小跑";
            start = Player.transform.position;
            firstShin = shin.localRotation;
            shinMotion = 0;
            yield return Steps(Vector3.left, true, 45, true);
            result.runDistance = PlanarDistance(start, Player.transform.position);
            result.runBoneDegrees = shinMotion;
            result.run = result.runDistance > 3.5f && shinMotion > 5 && ClipIs("Run");
            Capture("character-run.png");

            phase = "转向";
            yield return Steps(Vector3.right, false, 25, true);
            result.turn = Vector3.Dot(Player.Visual.forward, Vector3.right) > 0.9f;
            phase = "停步";
            yield return Steps(Vector3.zero, false, 20, true);

            Player.Teleport(Route.WallStart);
            phase = "墙体阻挡";
            yield return Steps(Route.WallDirection, false, 95, false);
            result.blockedSpeed = Player.ActualPlanarSpeed;
            result.wallStopsAnimation = result.blockedSpeed < 0.05f && ClipIs("Idle");
            Capture("character-wall-stop.png");

            Player.Teleport(Route.DockStart);
            phase = "码头通行";
            start = Player.transform.position;
            yield return Steps(Route.DockDirection, false, 85, false);
            result.dock = PlanarDistance(start, Player.transform.position) > 3 && Player.transform.position.y > 0.5f;
            Capture("character-dock.png");

            Player.Teleport(new Vector3(0, -8, 0));
            yield return null;
            yield return null;
            result.fallRecovery = Vector3.Distance(Player.transform.position, Player.Spawn) < 0.15f && Player.ActualPlanarSpeed == 0;
            Player.ResetPosition();
            yield return Steps(Vector3.zero, false, 15, false);
            active = false;
            experience.enabled = true;
            View.enabled = true;
            View.Overview = true;
            View.Snap();
            yield return new WaitForEndOfFrame();
            Capture("character-overview-day.png");
            experience.SetEvening(true);
            yield return null;
            yield return new WaitForEndOfFrame();
            Capture("character-overview-dusk.png");

            result.capturedFrames = frameIndex;
            result.passed = result.idle && result.walk && result.run && result.turn && result.wallStopsAnimation
                && result.dock && result.fallRecovery && result.groundContact;
            File.WriteAllText(Path.Combine(output, "character-result.json"), JsonUtility.ToJson(result, true));
            Debug.Log("HARBOR_CHARACTER_SMOKE " + JsonUtility.ToJson(result));
            Time.captureFramerate = 0;
            Application.Quit(result.passed ? 0 : 1);
        }

        private IEnumerator Steps(Vector3 direction, bool running, int count, bool record)
        {
            for (int frame = 0; frame < count; frame++)
            {
                Player.Drive(direction, running, 1f / 30);
                yield return null;
                View.transform.position = Player.transform.position + new Vector3(-3.2f, 2.2f, 4.6f);
                View.transform.LookAt(Player.transform.position + Vector3.up * 0.9f);
                yield return new WaitForEndOfFrame();
                shinMotion = Mathf.Max(shinMotion, Quaternion.Angle(firstShin, shin.localRotation));
                if (record) Capture(Path.Combine("frames", (++frameIndex).ToString("D4") + ".png"));
            }
        }

        private bool ClipIs(string name)
        {
            return Player.Locomotion.Animator.GetCurrentAnimatorClipInfo(0).Any(c => c.clip.name == name && c.weight > 0.98f);
        }

        private float FootGap()
        {
            if (!Physics.Raycast(Player.transform.position + Vector3.up * 0.3f, Vector3.down, out RaycastHit hit, 1, 1 << 8)) return 999;
            SkinnedMeshRenderer skin = Player.Visual.GetComponentInChildren<SkinnedMeshRenderer>();
            Mesh mesh = new Mesh();
            skin.BakeMesh(mesh);
            float minimum = mesh.vertices.Min(v => skin.transform.TransformPoint(v).y);
            Destroy(mesh);
            return minimum - hit.point.y;
        }

        private static float PlanarDistance(Vector3 a, Vector3 b)
        {
            a.y = b.y = 0;
            return Vector3.Distance(a, b);
        }

        private void Capture(string name)
        {
            Texture2D picture = ScreenCapture.CaptureScreenshotAsTexture();
            File.WriteAllBytes(Path.Combine(output, name), picture.EncodeToPNG());
            Destroy(picture);
        }

        private void OnGUI()
        {
            if (!active) return;
            if (caption == null)
            {
                caption = new GUIStyle(GUI.skin.label) { font = experience.InterfaceFont, fontSize = 20, alignment = TextAnchor.MiddleCenter };
                caption.normal.textColor = Color.white;
            }
            GUI.color = new Color(0.025f, 0.12f, 0.14f, 0.88f);
            GUI.DrawTexture(new Rect(Screen.width * 0.5f - 210, Screen.height - 66, 420, 44), Texture2D.whiteTexture);
            GUI.color = Color.white;
            GUI.Label(new Rect(Screen.width * 0.5f - 210, Screen.height - 66, 420, 44),
                phase + "  ·  实际速度 " + Player.ActualPlanarSpeed.ToString("F2") + " m/s", caption);
        }
    }
}
