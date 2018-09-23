module.exports = {
  moduleFileExtensions: [
    'js',
    'jsx',
    'esm',
    'esmx',
    "ts",
    "tsx",
    'json',
    'vue',
    'node',
  ],
  moduleDirectories: [
    "node_modules",
    "src"
  ],
  transform: {
    "^.+\\.tsx?$": "ts-jest",
    '^.+\\.vue$': 'vue-jest',
    '.+\\.(css|styl|less|sass|scss|svg|png|jpg|ttf|woff|woff2)$': 'jest-transform-stub',
    '^.+\\.jsx?$': 'babel-jest',
    '^.+\\.esm$': 'babel-jest',
  },
  // transformIgnorePatterns:[
    // "node_modules/(?!lodash-es)" // <-- this allows babel to load only the node modules I need (which is lodash-es) and ignore the rest
  // ],
  // testEnvironment: "node",
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  snapshotSerializers: [
    'jest-serializer-vue',
  ],
  testMatch: [
    '**/tests/unit/**/*.spec.(js|jsx|ts|tsx)|**/__tests__/*.(js|jsx|ts|tsx)',
  ],
  testURL: 'http://localhost/',
};
