import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "ThreatExchange",
  description:
    "Trust & Safety tools for working together to fight digital harms.",
  srcDir: "./content",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: "Welcome", link: "/" },
      {
        text: "Hashing Algorithms",
        items: [
          { text: "PDQ", link: "/hashing/pdq" },
          { text: "vPDQ", link: "/hashing/vpdq" },
          { text: "TMK", link: "/hashing/tmk" },
        ],
      },
      { text: "Python Library", link: "/pytx" },
      { text: "HMA", link: "/hma" },
      {
        text: "ThreatExchange Platform",
        link: "https://developers.facebook.com/docs/threat-exchange/",
        target: "_blank",
      },
    ],

    sidebar: {
      "/hashing/": [
        {
          text: "Hashing",
          link: "/",
          base: "/hashing/",
          items: [
            {
              text: "PDQ",
              link: "/",
              base: "/hashing/pdq/",
              items: [
                { text: "Algorithm", link: "/algorithm" },
                { text: "Implementations", link: "/implementations" },
              ],
            },
            { text: "vPDQ", base: "/hashing/vpdq/", link: "/" },
            { text: "TMK", base: "/hashing/tmk/", link: "/" },
          ],
        },
      ],
      "/hma/": [
        {
          text: "Hasher-Matcher-Actioner",
          link: "/",
          base: "/hma/",
          items: [
            { text: "Goals", base: "", link: "/goals" },
            { text: "Architecture", base: "", link: "/architecture" },
            { text: "History", base: "", link: "/history" },
            { text: "Roadmap", base: "", link: "/roadmap" },
            { text: "Using HMA", base: "", link: "/user-interface" },
            { text: "API Reference", base: "", link: "/api" },
          ],
        },
      ],
      "/pytx/": [
        {
          text: "Python-ThreatExchange",
          base: "/pytx/",
          items: [{ text: "Roadmap", link: "/roadmap" }],
        },
      ],
    },

    socialLinks: [
      { icon: "github", link: "https://github.com/facebook/threatexchange" },
    ],

    footer: {
      message:
        'Released under the <a href="https://github.com/facebook/ThreatExchange/blob/main/LICENSE">BSD License</a>. | <a href="https://opensource.facebook.com/legal/terms">Terms of Use</a> | <a href="https://opensource.facebook.com/legal/privacy">Privacy Policy</a>',
      copyright: "Copyright (c) Meta Platforms, Inc. and affiliates.",
    },

    search: {
      provider: "local",
    },
  },
});
