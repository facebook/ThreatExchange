// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'HMA',
  tagline: 'Hasher Matcher Actioner',
  url: 'https://facebook.github.io/',
  baseUrl: '/threatexchange/',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'facebook', // Usually your GitHub org/user name.
  projectName: 'ThreatExchange', // Usually your repo name.

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          // Please change this to your repo.
          editUrl: 'https://github.com/facebook/ThreatExchange/tree/main/hasher-matcher-actioner/docs/',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'HMA',
        items: [
          {
            type: 'doc',
            docId: 'installation/index',
            position: 'left',
            label: 'Install',
          },
          {
            type: 'doc',
            docId: 'guides/index',
            position: 'left',
            label: 'Usage',
          },
          {
            type: 'doc',
            docId: 'customizing/index',
            position: 'left',
            label: 'Customize',
          },
          {
            type: 'doc',
            docId: 'contributing/index',
            position: 'left',
            label: 'Contribute',
          },
          {
            href: 'https://github.com/facebook/ThreatExchange',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Guides',
            items: [
              {
                href: 'docs/installation',
                label: 'Install',
              },
              {
                href: 'docs/guides',
                label: 'Usage',
              },
              {
                href: 'docs/customizing',
                label: 'Customize',
              },
              {
                href: 'docs/contributing',
                label: 'Contribute',
              }
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/facebook/docusaurus',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Meta Platforms, Inc. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
};

module.exports = config;
