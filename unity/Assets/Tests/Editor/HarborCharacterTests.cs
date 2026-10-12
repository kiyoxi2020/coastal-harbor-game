using System.Linq;
using NUnit.Framework;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace CoastalHarbor.Tests
{
    public sealed class HarborCharacterTests
    {
        private const string Folder = "Assets/Characters/Returnee/";

        [Test]
        public void CharacterPrefabHasOneSkinnedMeshAndValidAnimator()
        {
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(Folder + "Returnee.prefab");
            Assert.That(prefab, Is.Not.Null, "Animated character prefab not created yet");
            var skins = prefab.GetComponentsInChildren<SkinnedMeshRenderer>();
            Assert.That(skins.Length, Is.EqualTo(1));
            Assert.That(skins[0].sharedMaterials.Length, Is.EqualTo(1));
            Assert.That(skins[0].bones.Length, Is.GreaterThanOrEqualTo(21));
            Animator animator = prefab.GetComponentInChildren<Animator>();
            Assert.That(animator, Is.Not.Null);
            Assert.That(animator.runtimeAnimatorController, Is.Not.Null);
            Assert.That(animator.avatar.isValid, Is.True);
            Assert.That(animator.applyRootMotion, Is.False);
        }

        [Test]
        public void ThreeLoopingClipsMoveTheSkeleton()
        {
            AnimationClip[] clips = AssetDatabase.LoadAllAssetsAtPath(Folder + "returnee.fbx")
                .OfType<AnimationClip>().Where(c => !c.name.StartsWith("__preview__")).ToArray();
            Assert.That(clips.Select(c => c.name), Is.EquivalentTo(new[] { "Idle", "Walk", "Run" }));
            foreach (AnimationClip clip in clips)
            {
                Assert.That(clip.isLooping, Is.True, clip.name);
                Assert.That(clip.length, Is.GreaterThan(0.6f));
            }
        }

        [Test]
        public void WalkerExposesMeasuredSpeedRatherThanInputMagnitude()
        {
            Assert.That(typeof(HarborWalker).GetProperty("ActualPlanarSpeed"), Is.Not.Null,
                "Locomotion must use collision-resolved movement speed");
        }

        [Test]
        public void AtlasCoordinatesCoverAllCharacterColors()
        {
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(Folder + "Returnee.prefab");
            Assert.That(prefab, Is.Not.Null);
            Mesh mesh = prefab.GetComponentInChildren<SkinnedMeshRenderer>().sharedMesh;
            Assert.That(mesh.uv.Distinct().Count(), Is.EqualTo(18));
            Assert.That(mesh.uv.All(uv => uv.x > 0 && uv.y > 0), Is.True,
                "Missing UV0 on merged parts would recolor facial features");
        }

        [Test]
        public void ImportedCharacterFacesForwardAndHasHumanScale()
        {
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(Folder + "Returnee.prefab");
            Assert.That(prefab, Is.Not.Null);
            GameObject instance = Object.Instantiate(prefab);
            Mesh baked = new Mesh();
            try
            {
                Transform marker = instance.GetComponentsInChildren<Transform>().Single(t => t.name == "ForwardMarker");
                Assert.That(marker.position.z, Is.GreaterThan(0.4f));
                Animator animator = instance.GetComponentInChildren<Animator>();
                AnimationClip idle = AssetDatabase.LoadAllAssetsAtPath(Folder + "returnee.fbx").OfType<AnimationClip>().Single(c => c.name == "Idle");
                idle.SampleAnimation(animator.gameObject, 0);
                SkinnedMeshRenderer skin = instance.GetComponentInChildren<SkinnedMeshRenderer>();
                skin.BakeMesh(baked);
                Vector3[] points = baked.vertices.Select(p => skin.transform.TransformPoint(p)).ToArray();
                float minimum = points.Min(p => p.y);
                float height = points.Max(p => p.y) - minimum;
                Assert.That(height, Is.InRange(1.55f, 1.85f));
                Assert.That(minimum, Is.InRange(-0.03f, 0.03f));
                Transform shin = instance.GetComponentsInChildren<Transform>().Single(t => t.name == "Shin.L");
                Quaternion before = shin.localRotation;
                AnimationClip walk = AssetDatabase.LoadAllAssetsAtPath(Folder + "returnee.fbx").OfType<AnimationClip>().Single(c => c.name == "Walk");
                walk.SampleAnimation(animator.gameObject, walk.length * 0.75f);
                Assert.That(Quaternion.Angle(before, shin.localRotation), Is.GreaterThan(5));
            }
            finally { Object.DestroyImmediate(baked); Object.DestroyImmediate(instance); }
        }

        [Test]
        public void MeasuredSpeedStopsAtWallAndResetsAfterTeleport()
        {
            GameObject player = new GameObject("Speed Test Player");
            GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Cube);
            GameObject wall = GameObject.CreatePrimitive(PrimitiveType.Cube);
            try
            {
                player.transform.position = new Vector3(100, 10, 100);
                floor.transform.position = new Vector3(100, 8.9f, 100);
                floor.transform.localScale = new Vector3(10, 0.2f, 10);
                wall.transform.position = new Vector3(100, 11, 100.8f);
                wall.transform.localScale = new Vector3(4, 6, 0.2f);
                HarborWalker walker = player.AddComponent<HarborWalker>();
                Physics.SyncTransforms();
                walker.Drive(Vector3.right, false, 0.02f);
                Assert.That(walker.ActualPlanarSpeed, Is.EqualTo(walker.WalkSpeed).Within(0.02));
                for (int i = 0; i < 45; i++) walker.Drive(Vector3.forward, false, 0.02f);
                Assert.That(walker.ActualPlanarSpeed, Is.LessThan(0.05f));
                walker.Teleport(new Vector3(100, 10, 100));
                Assert.That(walker.ActualPlanarSpeed, Is.Zero);
                walker.Drive(Vector3.one, false, 0);
                Assert.That(walker.ActualPlanarSpeed, Is.Zero);
            }
            finally { Object.DestroyImmediate(player); Object.DestroyImmediate(floor); Object.DestroyImmediate(wall); }
        }
    }
}
