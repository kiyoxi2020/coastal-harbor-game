using UnityEngine;

namespace CoastalHarbor
{
    public sealed class HarborExperience : MonoBehaviour
    {
        public HarborWalker Player;
        public HarborPoint[] Points;
        public Light Sun;
        public Material[] Windows;
        public Light[] MarketLights;
        public Font InterfaceFont;
        private HarborPoint nearest;
        private string message;
        private float messageUntil;
        private bool evening;
        private GUIStyle titleStyle;
        private GUIStyle bodyStyle;

        private void Awake()
        {
            Application.targetFrameRate = 60;
        }

        private void Update()
        {
            nearest = null;
            float best = float.PositiveInfinity;
            foreach (HarborPoint point in Points)
            {
                float distance = (point.transform.position - Player.transform.position).sqrMagnitude;
                if (point.InReach(Player.transform.position) && distance < best)
                {
                    nearest = point;
                    best = distance;
                }
            }
            if (Input.GetKeyDown(KeyCode.E) && nearest != null)
            {
                message = nearest.Description;
                messageUntil = Time.unscaledTime + 7;
            }
            if (Input.GetKeyDown(KeyCode.T)) SetEvening(!evening);
        }

        public void SetEvening(bool value)
        {
            evening = value;
            Sun.color = value ? new Color(1, 0.64f, 0.38f) : new Color(1, 0.95f, 0.82f);
            Sun.intensity = value ? 0.8f : 1.6f;
            RenderSettings.ambientLight = value ? new Color(0.18f, 0.26f, 0.38f) : new Color(0.57f, 0.68f, 0.70f);
            foreach (Material window in Windows)
                window.SetColor("_EmissionColor", new Color(1, 0.62f, 0.23f) * (value ? 2.5f : 0.2f));
            foreach (Light lamp in MarketLights) lamp.enabled = value;
        }

        private void OnGUI()
        {
            float scale = Mathf.Clamp(Screen.height / 900f, 0.7f, 1.5f);
            GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1));
            if (titleStyle == null)
            {
                Font font = InterfaceFont != null ? InterfaceFont : Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                titleStyle = new GUIStyle(GUI.skin.label) { font = font, fontSize = 24, fontStyle = FontStyle.Bold };
                titleStyle.normal.textColor = new Color(1, 0.92f, 0.72f);
                bodyStyle = new GUIStyle(GUI.skin.label) { font = font, fontSize = 16, wordWrap = true };
                bodyStyle.normal.textColor = Color.white;
            }
            GUI.color = new Color(0.035f, 0.14f, 0.16f, 0.90f);
            GUI.DrawTexture(new Rect(22, 22, 365, 190), Texture2D.whiteTexture);
            GUI.color = Color.white;
            GUI.Label(new Rect(40, 34, 330, 35), "潮港旧屋 · 漫步原型", titleStyle);
            GUI.Label(new Rect(40, 78, 330, 115), "WASD / 方向键：行走　Shift：小跑\n右键拖动：转动镜头　滚轮：缩放\nTab：总览 / 跟随　T：日景 / 黄昏\nE：查看附近地点　R：回到起点", bodyStyle);
            if (nearest != null || Time.unscaledTime < messageUntil)
            {
                float ypos = Screen.height / scale - 132;
                GUI.color = new Color(0.035f, 0.14f, 0.16f, 0.94f);
                GUI.DrawTexture(new Rect(22, ypos, 535, 105), Texture2D.whiteTexture);
                GUI.color = Color.white;
                string content = Time.unscaledTime < messageUntil ? message : "[E] " + nearest.Title;
                GUI.Label(new Rect(40, ypos + 14, 499, 90), content, bodyStyle);
            }
        }
    }
}
