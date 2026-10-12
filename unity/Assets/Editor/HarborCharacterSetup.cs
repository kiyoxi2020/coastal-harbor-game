using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace CoastalHarbor.Editor
{
    public static class HarborCharacterSetup
    {
        public const string Folder = "Assets/Characters/Returnee/";
        public const string PrefabPath = Folder + "Returnee.prefab";

        [Serializable] private sealed class ClipList { public ClipEntry[] clips; }
        [Serializable] private sealed class ClipEntry { public string name; public float nominalSpeed; }

        [MenuItem("Harbor/Create Animated Character")]
        public static void CreateAssets()
        {
            AssetDatabase.Refresh();
            ModelImporter importer = AssetImporter.GetAtPath(Folder + "returnee.fbx") as ModelImporter;
            if (importer == null) throw new InvalidOperationException("Export the Blender character first");
            importer.animationType = ModelImporterAnimationType.Generic;
            importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            importer.importAnimation = true;
            importer.importCameras = false;
            importer.importLights = false;
            importer.isReadable = true;
            importer.animationCompression = ModelImporterAnimationCompression.Off;
            importer.optimizeGameObjects = false;
            importer.motionNodeName = "Root";
            importer.SaveAndReimport();
            ModelImporterClipAnimation[] imported = importer.defaultClipAnimations;
            foreach (ModelImporterClipAnimation clip in imported)
            {
                string name = new[] { "Idle", "Walk", "Run" }.FirstOrDefault(n => clip.name.EndsWith(n, StringComparison.Ordinal));
                if (name == null) throw new InvalidOperationException("Unexpected FBX take: " + clip.name);
                clip.name = name;
                clip.loopTime = true;
                clip.loopPose = true;
                clip.lockRootRotation = true;
                clip.lockRootHeightY = true;
                clip.lockRootPositionXZ = true;
                clip.keepOriginalOrientation = true;
                clip.keepOriginalPositionY = true;
                clip.keepOriginalPositionXZ = true;
            }
            if (imported.Length != 3) throw new InvalidOperationException("Expected exactly three character actions");
            importer.clipAnimations = imported;
            importer.SaveAndReimport();

            Texture2D color = Texture("palette.png", true);
            Texture2D surface = Texture("surface.png", false);
            string materialPath = Folder + "ReturneePalette.mat";
            Material material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
            if (material == null)
            {
                material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
                AssetDatabase.CreateAsset(material, materialPath);
            }
            material.name = "ReturneePalette";
            material.SetColor("_BaseColor", Color.white);
            material.SetTexture("_BaseMap", color);
            material.SetTexture("_MetallicGlossMap", surface);
            material.SetFloat("_Metallic", 0);
            material.SetFloat("_Smoothness", 1);
            material.EnableKeyword("_METALLICSPECGLOSSMAP");
            EditorUtility.SetDirty(material);

            string controllerPath = Folder + "Returnee.controller";
            // This is a generated asset owned by this setup command.
            if (AssetDatabase.LoadAssetAtPath<AnimatorController>(controllerPath) != null)
                AssetDatabase.DeleteAsset(controllerPath);
            AnimatorController controller = AnimatorController.CreateAnimatorControllerAtPath(controllerPath);
            controller.AddParameter("Speed", AnimatorControllerParameterType.Float);
            AnimatorState state = controller.layers[0].stateMachine.AddState("Locomotion");
            controller.layers[0].stateMachine.defaultState = state;
            BlendTree tree = new BlendTree { name = "Measured Speed", blendType = BlendTreeType.Simple1D,
                blendParameter = "Speed", useAutomaticThresholds = false };
            AssetDatabase.AddObjectToAsset(tree, controller);
            AnimationClip[] clips = AssetDatabase.LoadAllAssetsAtPath(Folder + "returnee.fbx")
                .OfType<AnimationClip>().Where(c => !c.name.StartsWith("__preview__")).ToArray();
            ClipList source = JsonUtility.FromJson<ClipList>(File.ReadAllText(Folder + "clips.json"));
            string[] names = { "Idle", "Walk", "Run" };
            float[] speeds = { 0, HarborLocomotion.WalkMetersPerSecond, HarborLocomotion.RunMetersPerSecond };
            ChildMotion[] children = new ChildMotion[3];
            for (int i = 0; i < names.Length; i++)
            {
                float nominal = source.clips.First(c => c.name == names[i]).nominalSpeed;
                children[i] = new ChildMotion { motion = clips.Single(c => c.name == names[i]), threshold = speeds[i],
                    timeScale = i == 0 ? 1 : speeds[i] / nominal };
            }
            tree.children = children;
            state.motion = tree;
            EditorUtility.SetDirty(controller);

            GameObject wrapper = new GameObject("Returnee");
            try
            {
                GameObject model = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Folder + "returnee.fbx"));
                model.transform.SetParent(wrapper.transform, false);
                Transform marker = model.GetComponentsInChildren<Transform>().Single(t => t.name == "ForwardMarker");
                Vector3 forward = Vector3.ProjectOnPlane(marker.position - model.transform.position, Vector3.up).normalized;
                model.transform.localRotation = Quaternion.FromToRotation(forward, Vector3.forward);
                Animator animator = model.GetComponent<Animator>() ?? model.AddComponent<Animator>();
                animator.runtimeAnimatorController = controller;
                animator.applyRootMotion = false;
                animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
                foreach (SkinnedMeshRenderer skin in model.GetComponentsInChildren<SkinnedMeshRenderer>())
                {
                    skin.sharedMaterials = new[] { material };
                    skin.updateWhenOffscreen = true;
                    skin.localBounds = new Bounds(new Vector3(0, 0.9f, 0), new Vector3(2.4f, 2.4f, 2.4f));
                }
                PrefabUtility.SaveAsPrefabAsset(wrapper, PrefabPath);
            }
            finally { UnityEngine.Object.DestroyImmediate(wrapper); }
            AssetDatabase.SaveAssets();
            Debug.Log("HARBOR_CHARACTER_READY clips=" + string.Join(",", clips.Select(c => c.name + ":" + c.length)));
        }

        private static Texture2D Texture(string filename, bool srgb)
        {
            string path = Folder + filename;
            TextureImporter importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.sRGBTexture = srgb;
            importer.mipmapEnabled = false;
            importer.filterMode = FilterMode.Point;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.alphaSource = TextureImporterAlphaSource.FromInput;
            importer.alphaIsTransparency = false;
            importer.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }
    }
}
