using NUnit.Framework;
using UnityEditor.SceneManagement;
using UnityEngine;
using CoastalHarbor.Editor;

namespace CoastalHarbor.Tests
{
    public sealed class HarborTests
    {
        [Test]
        public void FourLineHelpFitsBundledChineseFont()
        {
            // Measure the fixed HUD layout against the actual font, not a Latin-font estimate.
            string source = System.IO.File.ReadAllText("Assets/Scripts/HarborExperience.cs");
            var label = System.Text.RegularExpressions.Regex.Match(source,
                @"GUI.Label\(new Rect\(40, 78, 330, (\d+)\), \""([^\""\r\n]+)\"", bodyStyle\)");
            Assert.That(label.Success, Is.True, "Help label layout could not be located");
            string help = label.Groups[2].Value.Replace("\\n", "\n");
            var style = new GUIStyle
            {
                font = UnityEditor.AssetDatabase.LoadAssetAtPath<Font>("Assets/Fonts/NotoSansCJKsc-Regular.otf"),
                fontSize = 16,
                wordWrap = true
            };
            float needed = style.CalcHeight(new GUIContent(help), 330);
            float available = float.Parse(label.Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture);
            Assert.That(available, Is.GreaterThanOrEqualTo(needed), "The last help line would be clipped");
        }

        [Test]
        public void DiagonalMovementIsNotFasterThanStraightMovement()
        {
            Assert.That(HarborWalker.CameraRelative(Vector2.one, Vector3.forward).magnitude, Is.EqualTo(1).Within(0.001));
        }

        [Test]
        public void MovementFollowsCameraHeadingWithoutVerticalDrift()
        {
            Vector3 direction = HarborWalker.CameraRelative(Vector2.up, new Vector3(1, -1, 0));
            Assert.That(Vector3.Distance(direction, Vector3.right), Is.LessThan(0.001));
        }

        [Test]
        public void SceneHasGroundUnderSpawnAndThirtyMappedMaterials()
        {
            EditorSceneManager.OpenScene(HarborSetup.ScenePath);
            HarborWalker player = Object.FindFirstObjectByType<HarborWalker>();
            Physics.SyncTransforms();
            Assert.That(Physics.Raycast(player.Spawn + Vector3.up, Vector3.down, 3, 1 << 8), Is.True);
            foreach (Renderer renderer in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                foreach (Material material in renderer.sharedMaterials)
                    Assert.That(material.shader.name, Is.EqualTo("Universal Render Pipeline/Lit"), renderer.name);
            Assert.That(UnityEditor.AssetDatabase.FindAssets("t:Material", new[] { "Assets/Materials" }).Length, Is.EqualTo(30));
        }

        [Test]
        public void InteractionIsLimitedToNearbyLocations()
        {
            GameObject target = new GameObject("Test Point");
            try
            {
                HarborPoint point = target.AddComponent<HarborPoint>();
                point.Radius = 1.5f;
                Assert.That(point.InReach(new Vector3(1, 0, 0)), Is.True);
                Assert.That(point.InReach(new Vector3(2, 0, 0)), Is.False);
            }
            finally { Object.DestroyImmediate(target); }
        }
    }
}
