using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace CoastalHarbor.Editor
{
    public static class HarborSetup
    {
        public const string ScenePath = "Assets/Scenes/Harbor.unity";
        private const string ArtPath = "Assets/Art/Harbor/";

        [Serializable] private sealed class Palette { public Entry[] materials; }
        [Serializable] private sealed class Entry
        {
            public string name;
            public float[] color;
            public float roughness;
            public float emission;
            public string texture;
        }

        [MenuItem("Harbor/Create Walkable Scene")]
        public static void CreateScene()
        {
            if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            string archive = "Assets/Scenes/Harbor-StaticArchive.unity";
            if (File.Exists(ScenePath) && !File.Exists(archive)) AssetDatabase.CopyAsset(ScenePath, archive);
            HarborCharacterSetup.CreateAssets();
            Directory.CreateDirectory("Assets/Scenes");
            Directory.CreateDirectory("Assets/Materials");
            AssetDatabase.Refresh();
            ModelImporter importer = (ModelImporter)AssetImporter.GetAtPath(ArtPath + "harbor.fbx");
            importer.importCameras = false;
            importer.importLights = false;
            importer.importAnimation = false;
            importer.isReadable = true;
            importer.SaveAndReimport();
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            GameObject model = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(ArtPath + "harbor.fbx"));
            PrefabUtility.UnpackPrefabInstance(model, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            model.name = "Harbor Art";
            Dictionary<string, Material> palette = BuildMaterials();
            Renderer[] renderers = model.GetComponentsInChildren<Renderer>();
            foreach (Renderer renderer in renderers)
            {
                renderer.sharedMaterials = renderer.sharedMaterials.Select(material =>
                {
                    if (!palette.TryGetValue(material.name, out Material replacement))
                        throw new InvalidOperationException("Missing material: " + material.name);
                    return replacement;
                }).ToArray();
            }

            Renderer house = renderers.First(renderer => renderer.name == "House walls");
            float xscale = house.bounds.center.x / -4.3f;
            float zscale = house.bounds.center.z / 4.2f;
            if (Mathf.Abs(Mathf.Abs(xscale) - 1) > 0.02f || Mathf.Abs(Mathf.Abs(zscale) - 1) > 0.02f)
                throw new InvalidOperationException("Unexpected FBX units or orientation: " + house.bounds);
            Vector3 Convert(float xpos, float ypos, float height) => new Vector3(xpos * xscale, height, ypos * zscale);

            GameObject collisionRoot = new GameObject("Simplified Collisions");
            string[] solids = { "Island foundation", "Garden ground", "Main lane", "Coastal lane", "House walls", "House stone plinth", "Raised vegetable bed", "Fish stall counter", "Tree trunk", "Entry step", "Dock board" };
            foreach (Renderer renderer in renderers)
            {
                if (!solids.Any(prefix => renderer.name.StartsWith(prefix, StringComparison.Ordinal))) continue;
                GameObject solid = new GameObject(renderer.name + " Collision");
                solid.transform.SetParent(collisionRoot.transform);
                solid.transform.position = renderer.bounds.center;
                solid.layer = 8;
                solid.isStatic = true;
                solid.AddComponent<BoxCollider>().size = renderer.bounds.size;
            }

            GameObject player = new GameObject("Player");
            player.transform.position = Convert(0.3f, -0.4f, 0.85f);
            CharacterController capsule = player.AddComponent<CharacterController>();
            capsule.height = 1.72f;
            capsule.radius = 0.23f;
            capsule.center = new Vector3(0, 0.86f, 0);
            capsule.stepOffset = 0.25f;
            capsule.skinWidth = 0.025f;
            capsule.minMoveDistance = 0;
            HarborWalker walker = player.AddComponent<HarborWalker>();
            walker.Spawn = player.transform.position;
            GameObject visual = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(HarborCharacterSetup.PrefabPath));
            visual.name = "Animated Player Visual";
            visual.transform.SetParent(player.transform, false);
            visual.transform.rotation = Quaternion.LookRotation(Convert(0, -1, 0));
            foreach (Renderer renderer in renderers.Where(renderer => renderer.name.StartsWith("Character", StringComparison.Ordinal)))
                renderer.gameObject.SetActive(false);
            visual.transform.localPosition = Vector3.zero;
            walker.Visual = visual.transform;
            walker.Locomotion = player.AddComponent<HarborLocomotion>();
            walker.Locomotion.Animator = visual.GetComponentInChildren<Animator>();

            foreach (Renderer renderer in model.GetComponentsInChildren<Renderer>()) renderer.gameObject.isStatic = true;
            GameObject cameraObject = new GameObject("Main Camera");
            cameraObject.tag = "MainCamera";
            Camera camera = cameraObject.AddComponent<Camera>();
            camera.fieldOfView = 36;
            camera.nearClipPlane = 0.1f;
            camera.farClipPlane = 300;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.32f, 0.65f, 0.72f);
            camera.allowHDR = true;
            cameraObject.AddComponent<AudioListener>();
            cameraObject.AddComponent<UniversalAdditionalCameraData>().renderPostProcessing = true;
            HarborCamera follow = cameraObject.AddComponent<HarborCamera>();
            follow.Target = player.transform;
            follow.InitialOffset = Convert(8, -10, 10);
            follow.OverviewPosition = Convert(17, -23, 19);
            follow.OverviewFocus = Convert(0, 0, 1);
            follow.Overview = false;
            follow.Snap();
            walker.View = camera.transform;

            Light sun = new GameObject("Afternoon Sun").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.transform.rotation = Quaternion.LookRotation(Convert(8, 6, -17));
            sun.shadows = LightShadows.Soft;
            sun.shadowBias = 0.02f;
            sun.shadowNormalBias = 0.2f;
            sun.shadowStrength = 0.7f;
            RenderSettings.sun = sun;
            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.fog = false;
            UniversalRenderPipelineAsset pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/Settings/PC_RPAsset.asset");
            pipeline.msaaSampleCount = 4;
            pipeline.shadowDistance = 60;
            GraphicsSettings.defaultRenderPipeline = pipeline;
            QualitySettings.renderPipeline = pipeline;
            QualitySettings.vSyncCount = 0;
            Application.targetFrameRate = 60;
            PlayerSettings.colorSpace = ColorSpace.Linear;

            string profilePath = "Assets/Settings/HarborVolume.asset";
            VolumeProfile profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(profilePath);
            if (profile == null)
            {
                profile = ScriptableObject.CreateInstance<VolumeProfile>();
                AssetDatabase.CreateAsset(profile, profilePath);
                Tonemapping tone = profile.Add<Tonemapping>(true);
                tone.mode.value = TonemappingMode.ACES;
                ColorAdjustments color = profile.Add<ColorAdjustments>(true);
                color.postExposure.value = -0.3f;
                color.saturation.value = -8;
                foreach (VolumeComponent component in profile.components) AssetDatabase.AddObjectToAsset(component, profile);
            }
            Volume volume = new GameObject("Harbor Color Grade").AddComponent<Volume>();
            volume.isGlobal = true;
            volume.sharedProfile = profile;

            HarborExperience experience = new GameObject("Harbor Experience").AddComponent<HarborExperience>();
            experience.Player = walker;
            experience.Sun = sun;
            experience.InterfaceFont = AssetDatabase.LoadAssetAtPath<Font>("Assets/Fonts/NotoSansCJKsc-Regular.otf");
            if (experience.InterfaceFont == null) throw new InvalidOperationException("Missing bundled Chinese font");
            experience.Windows = new[] { palette["Window"] };
            Light market = new GameObject("Market Warm Light").AddComponent<Light>();
            market.type = LightType.Point;
            market.transform.position = Convert(4.4f, 0.0f, 3.0f);
            market.color = new Color(1, 0.66f, 0.3f);
            market.intensity = 3;
            market.range = 6;
            experience.MarketLights = new[] { market };
            experience.Points = new[]
            {
                Point("祖辈留下的旧屋", "门牌 17 号。窗台的花还在，屋檐下多了一张等你坐下的长凳。", Convert(-4.3f, 0.7f, 0.85f), 1.5f),
                Point("后院菜园", "生菜与番茄已经长起来了。这里将成为种植与收获的第一块试验田。", Convert(-4.0f, -1.65f, 0.85f), 1.6f),
                Point("今日海鲜摊", "鱼、贝类和手写价签。交易系统尚未开放，今天先熟悉一下摊位。", Convert(4.4f, -0.65f, 0.85f), 1.6f),
                Point("小渔港码头", "木板在海风里轻响。渔船已经靠岸，往后可以从这里出海。", Convert(4.6f, -7, 0.8f), 1.8f)
            };
            experience.SetEvening(false);
            HarborSmoke smoke = new GameObject("Prototype Validation").AddComponent<HarborSmoke>();
            smoke.Player = walker;
            smoke.View = follow;
            smoke.WallStart = Convert(-4.3f, 0, 0.95f);
            smoke.WallDirection = Convert(0, 1, 0);
            smoke.DockStart = Convert(4.65f, -3.1f, 0.8f);
            smoke.DockDirection = Convert(0, -1, 0);
            HarborCharacterSmoke characterSmoke = new GameObject("Character Runtime Validation").AddComponent<HarborCharacterSmoke>();
            characterSmoke.Player = walker;
            characterSmoke.View = follow;
            characterSmoke.Route = smoke;
            Physics.SyncTransforms();
            if (!Physics.Raycast(player.transform.position + Vector3.up, Vector3.down, 3, 1 << 8))
                throw new InvalidOperationException("No ground under player spawn");
            EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene(), ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            AssetDatabase.SaveAssets();
            Debug.Log("HARBOR_SCENE_READY renderers=" + renderers.Length + " xscale=" + xscale + " zscale=" + zscale);
        }

        private static HarborPoint Point(string title, string description, Vector3 position, float radius)
        {
            HarborPoint point = new GameObject(title).AddComponent<HarborPoint>();
            point.transform.position = position;
            point.Title = title;
            point.Description = description;
            point.Radius = radius;
            return point;
        }

        private static Dictionary<string, Material> BuildMaterials()
        {
            Palette source = JsonUtility.FromJson<Palette>(File.ReadAllText(ArtPath + "materials.json"));
            Dictionary<string, Material> result = new Dictionary<string, Material>();
            foreach (Entry entry in source.materials)
            {
                string path = "Assets/Materials/" + entry.name + ".mat";
                Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
                bool create = material == null;
                if (create) material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
                material.name = entry.name;
                Color tint = new Color(entry.color[0], entry.color[1], entry.color[2], 1).gamma;
                material.SetColor("_BaseColor", string.IsNullOrEmpty(entry.texture) ? tint : Color.white);
                material.SetFloat("_Smoothness", 1 - entry.roughness);
                if (!string.IsNullOrEmpty(entry.texture))
                    material.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(ArtPath + entry.texture));
                if (entry.emission > 0)
                {
                    material.EnableKeyword("_EMISSION");
                    material.SetColor("_EmissionColor", tint * entry.emission);
                }
                if (create) AssetDatabase.CreateAsset(material, path);
                EditorUtility.SetDirty(material);
                result[entry.name] = material;
            }
            return result;
        }

        [MenuItem("Harbor/Build macOS Prototype")]
        public static void BuildMac()
        {
            Directory.CreateDirectory("Builds/macOS");
            BuildReport report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = "Builds/macOS/CoastalHarbor.app",
                target = BuildTarget.StandaloneOSX,
                options = BuildOptions.Development
            });
            if (report.summary.result != BuildResult.Succeeded)
                throw new InvalidOperationException("Build failed: " + report.summary.result);
            Debug.Log("HARBOR_BUILD_READY " + report.summary.totalSize);
        }
    }
}
