const { withAppBuildGradle } = require('expo/config-plugins');

/**
 * Pins the CMake version for the app's native (C++) build. Gradle downloads it into the Android SDK.
 *
 * Why: the default CMake 3.22.1 ships a ninja that can't open paths over 260 characters on Windows,
 * and React Native's generated object paths are longer than that. Newer CMake ships a ninja that can
 * (with Windows long paths enabled).
 */
module.exports = function withCmakeVersion(config, version) {
  return withAppBuildGradle(config, (cfg) => {
    const line = `version "${version}"`;
    if (!cfg.modResults.contents.includes(line)) {
      cfg.modResults.contents = cfg.modResults.contents.replace(
        /^android\s*\{/m,
        `android {\n    externalNativeBuild {\n        cmake {\n            ${line}\n        }\n    }\n`,
      );
    }
    return cfg;
  });
};
