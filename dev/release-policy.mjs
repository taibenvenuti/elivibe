const preset = "conventionalcommits";

// Load this policy explicitly; a default semantic-release CLI invocation is not a release path.
export const releasePolicy = {
  branches: ["main"],
  tagFormat: "v${version}",
  plugins: [
    ["@semantic-release/commit-analyzer", {
      preset,
      releaseRules: [
        // Match ignored commits before positive rules to prevent built-in defaults.
        { type: "*", release: false },
        { revert: true, release: false },
        { breaking: true, release: "major" },
        { type: "feat", release: "minor" },
        { type: "fix", release: "patch" },
      ],
    }],
    ["@semantic-release/release-notes-generator", { preset }],
  ],
};
