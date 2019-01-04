%{?scl:%scl_package nodejs}
%{!?scl:%global pkg_name %{name}}

%global with_debug 0

%{!?_with_bootstrap: %global bootstrap 1}

%{?!_pkgdocdir:%global _pkgdocdir %{_docdir}/%{pkg_name}-%{version}}

# ARM builds currently break on the Debug builds, so we'll just
# build the standard runtime until that gets sorted out.
%ifarch %{arm} aarch64 %{power64}
%global with_debug 0
%endif

# == Node.js Version ==
# Note: Fedora should only ship LTS versions of Node.js (currently expected
# to be major versions with even numbers). The odd-numbered versions are new
# feature releases that are only supported for nine months, which is shorter
# than a Fedora release lifecycle.
%global nodejs_major 10
%global nodejs_minor 10
%global nodejs_patch 0
%global nodejs_abi %{nodejs_major}.%{nodejs_minor}
%global nodejs_version %{nodejs_major}.%{nodejs_minor}.%{nodejs_patch}
%global nodejs_release 2

# == Bundled Dependency Versions ==
# v8 - from deps/v8/include/v8-version.h
%global v8_major 6
%global v8_minor 8
%global v8_build 275
%global v8_patch 30
# V8 presently breaks ABI at least every x.y release while never bumping SONAME
%global v8_abi %{v8_major}.%{v8_minor}
%global v8_version %{v8_major}.%{v8_minor}.%{v8_build}.%{v8_patch}

# c-ares - from deps/cares/include/ares_version.h
%global c_ares_major 1
%global c_ares_minor 14
%global c_ares_patch 0
%global c_ares_version %{c_ares_major}.%{c_ares_minor}.%{c_ares_patch}

# http-parser - from deps/http_parser/http_parser.h
%global http_parser_major 2
%global http_parser_minor 8
%global http_parser_patch 0
%global http_parser_version %{http_parser_major}.%{http_parser_minor}.%{http_parser_patch}

# libuv - from deps/uv/include/uv-version/h
%global libuv_major 1
%global libuv_minor 23
%global libuv_patch 0
%global libuv_version %{libuv_major}.%{libuv_minor}.%{libuv_patch}

# punycode - from lib/punycode.js
# Note: this was merged into the mainline since 0.6.x
# Note: this will be unmerged in v7 or v8
%global punycode_major 2
%global punycode_minor 1
%global punycode_patch 0
%global punycode_version %{punycode_major}.%{punycode_minor}.%{punycode_patch}

# npm - from deps/npm/package.json
%global npm_major 6
%global npm_minor 4
%global npm_patch 1
%global npm_version %{npm_major}.%{npm_minor}.%{npm_patch}

# In order to avoid needing to keep incrementing the release version for the
# main package forever, we will just construct one for npm that is guaranteed
# to increment safely. Changing this can only be done during an update when the
# base npm version number is increasing.
%global npm_release %{nodejs_major}.%{nodejs_minor}.%{nodejs_patch}.%{nodejs_release}

# Filter out the NPM bundled dependencies so we aren't providing them
%global __provides_exclude_from ^%{_prefix}/lib/node_modules/npm/.*$
%global __requires_exclude_from ^%{_prefix}/lib/node_modules/npm/.*$


Name: %{?scl_prefix}nodejs
Version: %{nodejs_version}
Release: %{nodejs_release}.bs1%{?dist}
Summary: JavaScript runtime
License: MIT and ASL 2.0 and ISC and BSD
Group: Development/Languages
URL: http://nodejs.org/

# nodejs bundles openssl, but we use the system version in Fedora
# because openssl contains prohibited code, we remove openssl completely from
# the tarball, using the script in Source100
Source0: node-v%{nodejs_version}-stripped.tar.gz
Source100: %{pkg_name}-tarball.sh

# The native module Requires generator remains in the nodejs SRPM, so it knows
# the nodejs and v8 versions.  The remainder has migrated to the
# nodejs-packaging SRPM.
Source7: nodejs_native.attr

# Disable running gyp on bundled deps we don't use
#Patch1: 0001-Disable-running-gyp-files-for-bundled-deps.patch

#Patch2: 0001-Fix-aarch64-debug.patch

# npm outputs ugly err when npm ls -g
#Patch3: 0001-fix-minizlib-dependency.patch

# Disable tests that are failing
# https://github.com/nodejs/help/issues/687
#Patch3: 0001-Disable-failed-tests.patch

# This is patch just for v10.1.0, we need to rebase it to later version
Patch1: 0001-Remove-OpenSSL-1.0.2-features.patch
Patch2: 0002-Remove-OpenSSL-1.0.2-features.patch

%{?scl:Requires: %{scl}-runtime}
%{?scl:BuildRequires: %{scl}-runtime}
BuildRequires: python-devel
#BuildRequires: libicu-devel
BuildRequires: zlib-devel
BuildRequires: devtoolset-7-gcc
BuildRequires: devtoolset-7-gcc-c++
# needed for tests
BuildRequires: procps-ng
BuildRequires: systemtap-sdt-devel


%if ! 0%{?bootstrap}
#BuildRequires: systemtap-sdt-devel
BuildRequires: %{?scl_prefix}http-parser-devel >= 2.7.0
%else
Provides: bundled(%{?scl_prefix}http-parser) = %{http_parser_version}
%endif

BuildRequires: openssl-devel >= 1:1.0.2

# we need the system certificate store when Patch2 is applied
Requires: ca-certificates

#we need ABI virtual provides where SONAMEs aren't enough/not present so deps
#break when binary compatibility is broken
Provides: %{?scl_prefix}nodejs(abi) = %{nodejs_abi}
Provides: %{?scl_prefix}nodejs(abi%{nodejs_major}) = %{nodejs_abi}
Provides: %{?scl_prefix}nodejs(v8-abi) = %{v8_abi}
Provides: %{?scl_prefix}nodejs(v8-abi%{v8_major}) = %{v8_abi}

#this corresponds to the "engine" requirement in package.json
Provides: %{?scl_prefix}nodejs(engine) = %{nodejs_version}

# Node.js currently has a conflict with the 'node' package in Fedora
# The ham-radio group has agreed to rename their binary for us, but
# in the meantime, we're setting an explicit Conflicts: here
Conflicts: node <= 0.3.2-12

# The punycode module was absorbed into the standard library in v0.6.
# It still exists as a seperate package for the benefit of users of older
# versions.  Since we've never shipped anything older than v0.10 in Fedora,
# we don't need the seperate nodejs-punycode package, so we Provide it here so
# dependent packages don't need to override the dependency generator.
# See also: RHBZ#11511811
# UPDATE: punycode will be deprecated and so we should unbundle it in Node v8
# and use upstream module instead
# https://github.com/nodejs/node/commit/29e49fc286080215031a81effbd59eac092fff2f
Provides: %{?scl_prefix}nodejs-punycode = %{punycode_version}
Provides: %{?scl_prefix}npm(punycode) = %{punycode_version}


# Node.js has forked c-ares from upstream in an incompatible way, so we need
# to carry the bundled version internally.
# See https://github.com/nodejs/node/commit/766d063e0578c0f7758c3a965c971763f43fec85
Provides: bundled(%{?scl_prefix}c-ares) = %{c_ares_version}

# Node.js is closely tied to the version of v8 that is used with it. It makes
# sense to use the bundled version because upstream consistently breaks ABI
# even in point releases. Node.js upstream has now removed the ability to build
# against a shared system version entirely.
# See https://github.com/nodejs/node/commit/d726a177ed59c37cf5306983ed00ecd858cfbbef
Provides: bundled(%{?scl_prefix}v8) = %{v8_version}

# Node.js and http-parser share an upstream. The http-parser upstream does not
# do releases often and is almost always far behind the bundled version
Provides: bundled(%{?scl_prefix}http-parser) = %{http_parser_version}

# We now bundle libuv in SCL too
Provides: bundled(%{?scl_prefix}libuv) = %{libuv_version}

# Node.js provides http2 support, but shared option is not yet available
Provides: bundled(%{?scl_prefix}nghttp2) = 1.25.0

# Make sure we keep NPM up to date when we update Node.js
Requires: %{?scl_prefix}npm = %{npm_version}-%{npm_release}.bs1%{?dist}

%description
Node.js is a platform built on Chrome's JavaScript runtime
for easily building fast, scalable network applications.
Node.js uses an event-driven, non-blocking I/O model that
makes it lightweight and efficient, perfect for data-intensive
real-time applications that run across distributed devices.


%package devel
Summary: JavaScript runtime - development headers
Group: Development/Languages
Requires: %{?scl_prefix}%{pkg_name}%{?_isa} = %{nodejs_version}-%{nodejs_release}.bs1%{?dist}
Requires: openssl-devel%{?_isa}
Requires: zlib-devel%{?_isa}
Requires: %{?scl_prefix}runtime

%if ! 0%{?bootstrap}
Requires: %{?scl_prefix}http-parser-devel%{?_isa}
%endif


%description devel
Development headers for the Node.js JavaScript runtime.


%package -n %{?scl_prefix}npm
Summary: Node.js Package Manager
Version: %{npm_version}
Release: %{npm_release}.bs1%{?dist}

# We used to ship npm separately, but it is so tightly integrated with Node.js
# (and expected to be present on all Node.js systems) that we ship it bundled
# now.
Provides: %{?scl_prefix}npm = %{npm_version}
Requires: %{?scl_prefix}nodejs = %{nodejs_version}-%{nodejs_release}.bs1%{?dist}

# Do not add epoch to the virtual NPM provides or it will break
# the automatic dependency-generation script.
Provides: %{?scl_prefix}npm(npm) = %{npm_version}

# Shipping each npm dependency as rpm is not very handy, so we bundle it now.
# However we still need to provide them in case there is a CVE
Provides: bundled(nodejs-JSONStream) = 1.3.1
Provides: bundled(nodejs-abbrev) = 1.1.1
Provides: bundled(nodejs-agent-base) = 4.1.1
Provides: bundled(nodejs-agent-base) = 4.1.2
Provides: bundled(nodejs-agentkeepalive) = 3.3.0
Provides: bundled(nodejs-ajv) = 5.2.3
Provides: bundled(nodejs-ansi-align) = 2.0.0
Provides: bundled(nodejs-ansi-regex) = 2.1.1
Provides: bundled(nodejs-ansi-regex) = 3.0.0
Provides: bundled(nodejs-ansi-styles) = 3.2.0
Provides: bundled(nodejs-ansicolors) = 0.3.2
Provides: bundled(nodejs-ansistyles) = 0.1.3
Provides: bundled(nodejs-aproba) = 1.2.0
Provides: bundled(nodejs-archy) = 1.0.0
Provides: bundled(nodejs-are-we-there-yet) = 1.1.4
Provides: bundled(nodejs-asap) = 2.0.5
Provides: bundled(nodejs-asn1) = 0.2.3
Provides: bundled(nodejs-assert-plus) = 1.0.0
Provides: bundled(nodejs-asynckit) = 0.4.0
Provides: bundled(nodejs-aws-sign2) = 0.7.0
Provides: bundled(nodejs-aws4) = 1.6.0
Provides: bundled(nodejs-balanced-match) = 1.0.0
Provides: bundled(nodejs-bcrypt-pbkdf) = 1.0.1
Provides: bundled(nodejs-bin-links) = 1.1.0
Provides: bundled(nodejs-block-stream) = 0.0.9
Provides: bundled(nodejs-bluebird) = 3.5.1
Provides: bundled(nodejs-boom) = 4.3.1
Provides: bundled(nodejs-boom) = 5.2.0
Provides: bundled(nodejs-boxen) = 1.2.1
Provides: bundled(nodejs-brace-expansion) = 1.1.8
Provides: bundled(nodejs-builtin-modules) = 1.1.1
Provides: bundled(nodejs-builtins) = 1.0.3
Provides: bundled(nodejs-byline) = 5.0.0
Provides: bundled(nodejs-cacache) = 10.0.1
Provides: bundled(nodejs-cacache) = 9.3.0
Provides: bundled(nodejs-call-limit) = 1.1.0
Provides: bundled(nodejs-camelcase) = 4.1.0
Provides: bundled(nodejs-capture-stack-trace) = 1.0.0
Provides: bundled(nodejs-caseless) = 0.12.0
Provides: bundled(nodejs-chalk) = 2.1.0
Provides: bundled(nodejs-chownr) = 1.0.1
Provides: bundled(nodejs-cidr-regex) = 1.0.6
Provides: bundled(nodejs-cli-boxes) = 1.0.0
Provides: bundled(nodejs-cli-table2) = 0.2.0
Provides: bundled(nodejs-cliui) = 3.2.0
Provides: bundled(nodejs-clone) = 1.0.2
Provides: bundled(nodejs-cmd-shim) = 2.0.2
Provides: bundled(nodejs-co) = 4.6.0
Provides: bundled(nodejs-code-point-at) = 1.1.0
Provides: bundled(nodejs-color-convert) = 1.9.0
Provides: bundled(nodejs-color-name) = 1.1.3
Provides: bundled(nodejs-colors) = 1.1.2
Provides: bundled(nodejs-columnify) = 1.5.4
Provides: bundled(nodejs-combined-stream) = 1.0.5
Provides: bundled(nodejs-concat-map) = 0.0.1
Provides: bundled(nodejs-concat-stream) = 1.6.0
Provides: bundled(nodejs-config-chain) = 1.1.11
Provides: bundled(nodejs-configstore) = 3.1.1
Provides: bundled(nodejs-console-control-strings) = 1.1.0
Provides: bundled(nodejs-copy-concurrently) = 1.0.5
Provides: bundled(nodejs-core-util-is) = 1.0.2
Provides: bundled(nodejs-create-error-class) = 3.0.2
Provides: bundled(nodejs-cross-spawn) = 5.1.0
Provides: bundled(nodejs-cryptiles) = 3.1.2
Provides: bundled(nodejs-crypto-random-string) = 1.0.0
Provides: bundled(nodejs-cyclist) = 0.2.2
Provides: bundled(nodejs-dashdash) = 1.14.1
Provides: bundled(nodejs-debug) = 2.6.9
Provides: bundled(nodejs-debuglog) = 1.0.1
Provides: bundled(nodejs-decamelize) = 1.2.0
Provides: bundled(nodejs-decode-uri-component) = 0.2.0
Provides: bundled(nodejs-deep-extend) = 0.4.2
Provides: bundled(nodejs-defaults) = 1.0.3
Provides: bundled(nodejs-delayed-stream) = 1.0.0
Provides: bundled(nodejs-delegates) = 1.0.0
Provides: bundled(nodejs-detect-indent) = 5.0.0
Provides: bundled(nodejs-dezalgo) = 1.0.3
Provides: bundled(nodejs-dot-prop) = 4.2.0
Provides: bundled(nodejs-dotenv) = 4.0.0
Provides: bundled(nodejs-duplexer3) = 0.1.4
Provides: bundled(nodejs-duplexify) = 3.5.0
Provides: bundled(nodejs-ecc-jsbn) = 0.1.1
Provides: bundled(nodejs-editor) = 1.0.0
Provides: bundled(nodejs-encoding) = 0.1.12
Provides: bundled(nodejs-end-of-stream) = 1.0.0
Provides: bundled(nodejs-end-of-stream) = 1.4.0
Provides: bundled(nodejs-err-code) = 1.1.2
Provides: bundled(nodejs-errno) = 0.1.4
Provides: bundled(nodejs-error-ex) = 1.3.1
Provides: bundled(nodejs-es6-promise) = 4.1.1
Provides: bundled(nodejs-es6-promisify) = 5.0.0
Provides: bundled(nodejs-escape-string-regexp) = 1.0.5
Provides: bundled(nodejs-execa) = 0.7.0
Provides: bundled(nodejs-extend) = 3.0.1
Provides: bundled(nodejs-extsprintf) = 1.3.0
Provides: bundled(nodejs-fast-deep-equal) = 1.0.0
Provides: bundled(nodejs-find-npm-prefix) = 1.0.1
Provides: bundled(nodejs-find-up) = 2.1.0
Provides: bundled(nodejs-flush-write-stream) = 1.0.2
Provides: bundled(nodejs-forever-agent) = 0.6.1
Provides: bundled(nodejs-form-data) = 2.3.1
Provides: bundled(nodejs-from2) = 1.3.0
Provides: bundled(nodejs-from2) = 2.3.0
Provides: bundled(nodejs-fs-vacuum) = 1.2.10
Provides: bundled(nodejs-fs-write-stream-atomic) = 1.0.10
Provides: bundled(nodejs-fs.realpath) = 1.0.0
Provides: bundled(nodejs-fstream) = 1.0.11
Provides: bundled(nodejs-gauge) = 2.7.4
Provides: bundled(nodejs-genfun) = 4.0.1
Provides: bundled(nodejs-gentle-fs) = 2.0.1
Provides: bundled(nodejs-get-caller-file) = 1.0.2
Provides: bundled(nodejs-get-stream) = 3.0.0
Provides: bundled(nodejs-getpass) = 0.1.7
Provides: bundled(nodejs-glob) = 7.1.2
Provides: bundled(nodejs-global-dirs) = 0.1.0
Provides: bundled(nodejs-got) = 6.7.1
Provides: bundled(nodejs-graceful-fs) = 4.1.11
Provides: bundled(nodejs-har-schema) = 2.0.0
Provides: bundled(nodejs-har-validator) = 5.0.3
Provides: bundled(nodejs-has-flag) = 2.0.0
Provides: bundled(nodejs-has-unicode) = 2.0.1
Provides: bundled(nodejs-hawk) = 6.0.2
Provides: bundled(nodejs-hoek) = 4.2.0
Provides: bundled(nodejs-hosted-git-info) = 2.5.0
Provides: bundled(nodejs-http-cache-semantics) = 3.8.0
Provides: bundled(nodejs-http-proxy-agent) = 2.0.0
Provides: bundled(nodejs-http-signature) = 1.2.0
Provides: bundled(nodejs-https-proxy-agent) = 2.1.0
Provides: bundled(nodejs-humanize-ms) = 1.2.1
Provides: bundled(nodejs-iconv-lite) = 0.4.19
Provides: bundled(nodejs-iferr) = 0.1.5
Provides: bundled(nodejs-ignore-walk) = 3.0.1
Provides: bundled(nodejs-import-lazy) = 2.1.0
Provides: bundled(nodejs-imurmurhash) = 0.1.4
Provides: bundled(nodejs-inflight) = 1.0.6
Provides: bundled(nodejs-inherits) = 2.0.3
Provides: bundled(nodejs-ini) = 1.3.4
Provides: bundled(nodejs-init-package-json) = 1.10.1
Provides: bundled(nodejs-invert-kv) = 1.0.0
Provides: bundled(nodejs-ip) = 1.1.5
Provides: bundled(nodejs-is-arrayish) = 0.2.1
Provides: bundled(nodejs-is-builtin-module) = 1.0.0
Provides: bundled(nodejs-is-cidr) = 1.0.0
Provides: bundled(nodejs-is-fullwidth-code-point) = 1.0.0
Provides: bundled(nodejs-is-fullwidth-code-point) = 2.0.0
Provides: bundled(nodejs-is-installed-globally) = 0.1.0
Provides: bundled(nodejs-is-npm) = 1.0.0
Provides: bundled(nodejs-is-obj) = 1.0.1
Provides: bundled(nodejs-is-path-inside) = 1.0.0
Provides: bundled(nodejs-is-redirect) = 1.0.0
Provides: bundled(nodejs-is-retry-allowed) = 1.1.0
Provides: bundled(nodejs-is-stream) = 1.1.0
Provides: bundled(nodejs-is-typedarray) = 1.0.0
Provides: bundled(nodejs-isarray) = 0.0.1
Provides: bundled(nodejs-isarray) = 1.0.0
Provides: bundled(nodejs-isexe) = 2.0.0
Provides: bundled(nodejs-isstream) = 0.1.2
Provides: bundled(nodejs-jsbn) = 0.1.1
Provides: bundled(nodejs-json-parse-better-errors) = 1.0.1
Provides: bundled(nodejs-json-schema) = 0.2.3
Provides: bundled(nodejs-json-schema-traverse) = 0.3.1
Provides: bundled(nodejs-json-stable-stringify) = 1.0.1
Provides: bundled(nodejs-json-stringify-safe) = 5.0.1
Provides: bundled(nodejs-jsonify) = 0.0.0
Provides: bundled(nodejs-jsonparse) = 1.3.1
Provides: bundled(nodejs-jsprim) = 1.4.1
Provides: bundled(nodejs-latest-version) = 3.1.0
Provides: bundled(nodejs-lazy-property) = 1.0.0
Provides: bundled(nodejs-lcid) = 1.0.0
Provides: bundled(nodejs-libnpx) = 9.7.1
Provides: bundled(nodejs-load-json-file) = 2.0.0
Provides: bundled(nodejs-locate-path) = 2.0.0
Provides: bundled(nodejs-lockfile) = 1.0.3
Provides: bundled(nodejs-lodash) = 3.10.1
Provides: bundled(nodejs-lodash._baseindexof) = 3.1.0
Provides: bundled(nodejs-lodash._baseuniq) = 4.6.0
Provides: bundled(nodejs-lodash._bindcallback) = 3.0.1
Provides: bundled(nodejs-lodash._cacheindexof) = 3.0.2
Provides: bundled(nodejs-lodash._createcache) = 3.1.2
Provides: bundled(nodejs-lodash._createset) = 4.0.3
Provides: bundled(nodejs-lodash._getnative) = 3.9.1
Provides: bundled(nodejs-lodash._root) = 3.0.1
Provides: bundled(nodejs-lodash.clonedeep) = 4.5.0
Provides: bundled(nodejs-lodash.restparam) = 3.6.1
Provides: bundled(nodejs-lodash.union) = 4.6.0
Provides: bundled(nodejs-lodash.uniq) = 4.5.0
Provides: bundled(nodejs-lodash.without) = 4.4.0
Provides: bundled(nodejs-lowercase-keys) = 1.0.0
Provides: bundled(nodejs-lru-cache) = 4.1.1
Provides: bundled(nodejs-make-dir) = 1.0.0
Provides: bundled(nodejs-make-fetch-happen) = 2.5.0
Provides: bundled(nodejs-make-fetch-happen) = 2.6.0
Provides: bundled(nodejs-meant) = 1.0.1
Provides: bundled(nodejs-mem) = 1.1.0
Provides: bundled(nodejs-mime-db) = 1.30.0
Provides: bundled(nodejs-mime-types) = 2.1.17
Provides: bundled(nodejs-mimic-fn) = 1.1.0
Provides: bundled(nodejs-minimatch) = 3.0.4
Provides: bundled(nodejs-minimist) = 0.0.8
Provides: bundled(nodejs-minimist) = 1.2.0
Provides: bundled(nodejs-minipass) = 2.2.1
Provides: bundled(nodejs-minizlib) = 1.0.4
Provides: bundled(nodejs-mississippi) = 1.3.0
Provides: bundled(nodejs-mkdirp) = 0.5.1
Provides: bundled(nodejs-move-concurrently) = 1.0.1
Provides: bundled(nodejs-ms) = 2.0.0
Provides: bundled(nodejs-mute-stream) = 0.0.7
Provides: bundled(nodejs-node-fetch-npm) = 2.0.2
Provides: bundled(nodejs-node-gyp) = 3.6.2
Provides: bundled(nodejs-nopt) = 3.0.6
Provides: bundled(nodejs-nopt) = 4.0.1
Provides: bundled(nodejs-normalize-package-data) = 2.4.0
Provides: bundled(nodejs-npm) = 5.6.0 /root/npm/node_modules/npm
Provides: bundled(nodejs-npm-bundled) = 1.0.3
Provides: bundled(nodejs-npm-cache-filename) = 1.0.2
Provides: bundled(nodejs-npm-install-checks) = 3.0.0
Provides: bundled(nodejs-npm-lifecycle) = 2.0.0
Provides: bundled(nodejs-npm-package-arg) = 5.1.2
Provides: bundled(nodejs-npm-package-arg) = 6.0.0
Provides: bundled(nodejs-npm-packlist) = 1.1.10
Provides: bundled(nodejs-npm-pick-manifest) = 2.1.0
Provides: bundled(nodejs-npm-profile) = 2.0.5
Provides: bundled(nodejs-npm-registry-client) = 8.5.0
Provides: bundled(nodejs-npm-run-path) = 2.0.2
Provides: bundled(nodejs-npm-user-validate) = 1.0.0
Provides: bundled(nodejs-npmlog) = 4.1.2
Provides: bundled(nodejs-number-is-nan) = 1.0.1
Provides: bundled(nodejs-oauth-sign) = 0.8.2
Provides: bundled(nodejs-object-assign) = 4.1.1
Provides: bundled(nodejs-once) = 1.3.3
Provides: bundled(nodejs-once) = 1.4.0
Provides: bundled(nodejs-opener) = 1.4.3
Provides: bundled(nodejs-os-homedir) = 1.0.2
Provides: bundled(nodejs-os-locale) = 2.1.0
Provides: bundled(nodejs-os-tmpdir) = 1.0.2
Provides: bundled(nodejs-osenv) = 0.1.4
Provides: bundled(nodejs-p-finally) = 1.0.0
Provides: bundled(nodejs-p-limit) = 1.1.0
Provides: bundled(nodejs-p-locate) = 2.0.0
Provides: bundled(nodejs-package-json) = 4.0.1
Provides: bundled(nodejs-pacote) = 7.0.2
Provides: bundled(nodejs-parallel-transform) = 1.1.0
Provides: bundled(nodejs-parse-json) = 2.2.0
Provides: bundled(nodejs-path-exists) = 3.0.0
Provides: bundled(nodejs-path-is-absolute) = 1.0.1
Provides: bundled(nodejs-path-is-inside) = 1.0.2
Provides: bundled(nodejs-path-key) = 2.0.1
Provides: bundled(nodejs-path-type) = 2.0.0
Provides: bundled(nodejs-performance-now) = 2.1.0
Provides: bundled(nodejs-pify) = 2.3.0
Provides: bundled(nodejs-prepend-http) = 1.0.4
Provides: bundled(nodejs-process-nextick-args) = 1.0.7
Provides: bundled(nodejs-promise-inflight) = 1.0.1
Provides: bundled(nodejs-promise-retry) = 1.1.1
Provides: bundled(nodejs-promzard) = 0.3.0
Provides: bundled(nodejs-proto-list) = 1.2.4
Provides: bundled(nodejs-protoduck) = 4.0.0
Provides: bundled(nodejs-prr) = 0.0.0
Provides: bundled(nodejs-pseudomap) = 1.0.2
Provides: bundled(nodejs-pump) = 1.0.2
Provides: bundled(nodejs-pumpify) = 1.3.5
Provides: bundled(nodejs-punycode) = 1.4.1
Provides: bundled(nodejs-qrcode-terminal) = 0.11.0
Provides: bundled(nodejs-qs) = 6.5.1
Provides: bundled(nodejs-query-string) = 5.0.1
Provides: bundled(nodejs-qw) = 1.0.1
Provides: bundled(nodejs-rc) = 1.2.1
Provides: bundled(nodejs-read) = 1.0.7
Provides: bundled(nodejs-read-cmd-shim) = 1.0.1
Provides: bundled(nodejs-read-installed) = 4.0.3
Provides: bundled(nodejs-read-package-json) = 2.0.12
Provides: bundled(nodejs-read-package-tree) = 5.1.6
Provides: bundled(nodejs-read-pkg) = 2.0.0
Provides: bundled(nodejs-read-pkg-up) = 2.0.0
Provides: bundled(nodejs-readable-stream) = 1.1.14
Provides: bundled(nodejs-readable-stream) = 2.3.3
Provides: bundled(nodejs-readdir-scoped-modules) = 1.0.2
Provides: bundled(nodejs-registry-auth-token) = 3.3.1
Provides: bundled(nodejs-registry-url) = 3.1.0
Provides: bundled(nodejs-request) = 2.83.0
Provides: bundled(nodejs-require-directory) = 2.1.1
Provides: bundled(nodejs-require-main-filename) = 1.0.1
Provides: bundled(nodejs-resolve-from) = 4.0.0
Provides: bundled(nodejs-retry) = 0.10.1
Provides: bundled(nodejs-rimraf) = 2.6.2
Provides: bundled(nodejs-run-queue) = 1.0.3
Provides: bundled(nodejs-safe-buffer) = 5.1.1
Provides: bundled(nodejs-semver) = 5.3.0
Provides: bundled(nodejs-semver) = 5.4.1
Provides: bundled(nodejs-semver-diff) = 2.1.0
Provides: bundled(nodejs-set-blocking) = 2.0.0
Provides: bundled(nodejs-sha) = 2.0.1
Provides: bundled(nodejs-shebang-command) = 1.2.0
Provides: bundled(nodejs-shebang-regex) = 1.0.0
Provides: bundled(nodejs-signal-exit) = 3.0.2
Provides: bundled(nodejs-slash) = 1.0.0
Provides: bundled(nodejs-slide) = 1.1.6
Provides: bundled(nodejs-smart-buffer) = 1.1.15
Provides: bundled(nodejs-sntp) = 2.0.2
Provides: bundled(nodejs-socks) = 1.1.10
Provides: bundled(nodejs-socks-proxy-agent) = 3.0.1
Provides: bundled(nodejs-sorted-object) = 2.0.1
Provides: bundled(nodejs-sorted-union-stream) = 2.1.3
Provides: bundled(nodejs-spdx-correct) = 1.0.2
Provides: bundled(nodejs-spdx-expression-parse) = 1.0.4
Provides: bundled(nodejs-spdx-license-ids) = 1.2.2
Provides: bundled(nodejs-sshpk) = 1.13.1
Provides: bundled(nodejs-ssri) = 4.1.6
Provides: bundled(nodejs-ssri) = 5.0.0
Provides: bundled(nodejs-stream-each) = 1.2.0
Provides: bundled(nodejs-stream-iterate) = 1.2.0
Provides: bundled(nodejs-stream-shift) = 1.0.0
Provides: bundled(nodejs-strict-uri-encode) = 1.1.0
Provides: bundled(nodejs-string-width) = 1.0.2
Provides: bundled(nodejs-string-width) = 2.1.1
Provides: bundled(nodejs-string_decoder) = 0.10.31
Provides: bundled(nodejs-string_decoder) = 1.0.3
Provides: bundled(nodejs-stringstream) = 0.0.5
Provides: bundled(nodejs-strip-ansi) = 3.0.1
Provides: bundled(nodejs-strip-ansi) = 4.0.0
Provides: bundled(nodejs-strip-bom) = 3.0.0
Provides: bundled(nodejs-strip-eof) = 1.0.0
Provides: bundled(nodejs-strip-json-comments) = 2.0.1
Provides: bundled(nodejs-supports-color) = 4.4.0
Provides: bundled(nodejs-tar) = 2.2.1
Provides: bundled(nodejs-tar) = 4.0.2
Provides: bundled(nodejs-term-size) = 1.2.0
Provides: bundled(nodejs-text-table) = 0.2.0
Provides: bundled(nodejs-through) = 2.3.8
Provides: bundled(nodejs-through2) = 2.0.3
Provides: bundled(nodejs-timed-out) = 4.0.1
Provides: bundled(nodejs-tough-cookie) = 2.3.3
Provides: bundled(nodejs-tunnel-agent) = 0.6.0
Provides: bundled(nodejs-tweetnacl) = 0.14.5
Provides: bundled(nodejs-typedarray) = 0.0.6
Provides: bundled(nodejs-uid-number) = 0.0.6
Provides: bundled(nodejs-umask) = 1.1.0
Provides: bundled(nodejs-unique-filename) = 1.1.0
Provides: bundled(nodejs-unique-slug) = 2.0.0
Provides: bundled(nodejs-unique-string) = 1.0.0
Provides: bundled(nodejs-unpipe) = 1.0.0
Provides: bundled(nodejs-unzip-response) = 2.0.1
Provides: bundled(nodejs-update-notifier) = 2.3.0
Provides: bundled(nodejs-url-parse-lax) = 1.0.0
Provides: bundled(nodejs-util-deprecate) = 1.0.2
Provides: bundled(nodejs-util-extend) = 1.0.3
Provides: bundled(nodejs-uuid) = 3.1.0
Provides: bundled(nodejs-validate-npm-package-license) = 3.0.1
Provides: bundled(nodejs-validate-npm-package-name) = 3.0.0
Provides: bundled(nodejs-verror) = 1.10.0
Provides: bundled(nodejs-wcwidth) = 1.0.1
Provides: bundled(nodejs-which) = 1.3.0
Provides: bundled(nodejs-which-module) = 2.0.0
Provides: bundled(nodejs-wide-align) = 1.1.2
Provides: bundled(nodejs-widest-line) = 1.0.0
Provides: bundled(nodejs-worker-farm) = 1.5.1
Provides: bundled(nodejs-wrap-ansi) = 2.1.0
Provides: bundled(nodejs-wrappy) = 1.0.2
Provides: bundled(nodejs-write-file-atomic) = 2.1.0
Provides: bundled(nodejs-xdg-basedir) = 3.0.0
Provides: bundled(nodejs-xtend) = 4.0.1
Provides: bundled(nodejs-y18n) = 3.2.1
Provides: bundled(nodejs-yallist) = 2.1.2
Provides: bundled(nodejs-yallist) = 3.0.2
Provides: bundled(nodejs-yargs) = 8.0.2
Provides: bundled(nodejs-yargs-parser) = 7.0.0


%description -n %{?scl_prefix}npm
npm is a package manager for node.js. You can use it to install and publish
your node programs. It manages dependencies and does other cool stuff.


%package docs
Summary: Node.js API documentation
Group: Documentation
BuildArch: noarch

%description docs
The API documentation for the Node.js JavaScript runtime.


%prep
%setup -q -n node-v%{nodejs_version}

# remove bundled dependencies that we aren't building
#%patch1 -p1

# fix outdated minizlib modules in npm node_modules tree
#%%patch3 -p1

# rm -rf deps/zlib

# OpenSSL patches
%patch1 -p1
%patch2 -p1


%build

%{?scl:scl enable %{scl} devtoolset-7 - << \EOF}

set -ex
# build with debugging symbols and add defines from libuv (#892601)
# Node's v8 breaks with GCC 6 because of incorrect usage of methods on
# NULL objects. We need to pass -fno-delete-null-pointer-checks
export CFLAGS='%{optflags} -g \
               -D_LARGEFILE_SOURCE \
               -D_FILE_OFFSET_BITS=64 \
               -DZLIB_CONST \
               -fno-delete-null-pointer-checks'
export CXXFLAGS='%{optflags} -g \
                 -D_LARGEFILE_SOURCE \
                 -D_FILE_OFFSET_BITS=64 \
                 -DZLIB_CONST \
                 -fno-delete-null-pointer-checks'

# Explicit new lines in C(XX)FLAGS can break naive build scripts
export CFLAGS="$(echo ${CFLAGS} | tr '\n\\' '  ')"
export CXXFLAGS="$(echo ${CXXFLAGS} | tr '\n\\' '  ')"

%if ! 0%{?bootstrap}
./configure --prefix=%{_prefix} \
           --shared-openssl \
           --shared-zlib \
           --shared-http-parser \
           --with-dtrace \
           --debug-nghttp2 \
           --openssl-use-def-ca-store
%else
./configure --prefix=%{_prefix} \
           --shared-openssl \
           --shared-zlib \
           --with-dtrace \
           --debug-nghttp2 \
           --openssl-use-def-ca-store
%endif

make BUILDTYPE=Release %{?_smp_mflags}
%if 0%{?with_debug} == 1
make BUILDTYPE=Debug %{?_smp_mflags}
%endif

%{?scl:EOF}


%install
./tools/install.py install %{buildroot} %{_prefix}

# Set the binary permissions properly
chmod 0755 %{buildroot}/%{_bindir}/node

%if 0%{?with_debug} == 1
# Install the debug binary and set its permissions
install -Dpm0755 out/Debug/node %{buildroot}/%{_bindir}/node_g
%endif

# own the sitelib directory
mkdir -p %{buildroot}%{_prefix}/lib/node_modules

# ensure Requires are added to every native module that match the Provides from
# the nodejs build in the buildroot
#install -Dpm0644 %{SOURCE7} %{buildroot}%{_rpmconfigdir}/fileattrs/nodejs_native.attr
#cat << EOF > %{buildroot}%{_rpmconfigdir}/nodejs_native.req
#!/bin/sh
#echo 'nodejs(abi%{nodejs_major}) >= %nodejs_abi'
#echo 'nodejs(v8-abi%{v8_major}) >= %v8_abi'
#EOF
#chmod 0755 %{buildroot}%{_rpmconfigdir}/nodejs_native.req

#install documentation
mkdir -p %{buildroot}%{_pkgdocdir}/html
cp -pr doc/* %{buildroot}%{_pkgdocdir}/html
rm -f %{buildroot}%{_pkgdocdir}/html/nodejs.1

#node-gyp needs common.gypi too
mkdir -p %{buildroot}%{_datadir}/node
cp -p common.gypi %{buildroot}%{_datadir}/node

# Install the GDB init tool into the documentation directory
mv %{buildroot}/%{_datadir}/doc/node/gdbinit %{buildroot}/%{_pkgdocdir}/gdbinit

# Install LLDB into documentation directory
mv %{buildroot}/%{_datadir}/doc/node/lldbinit %{buildroot}/%{_pkgdocdir}/lldbinit
mv %{buildroot}/%{_datadir}/doc/node/lldb_commands.py %{buildroot}/%{_pkgdocdir}/lldb_commands.py

# Since the old version of NPM was unbundled, there are a lot of symlinks in
# it's node_modules directory. We need to keep these as symlinks to ensure we
# can backtrack on this if we decide to.

# Rename the npm node_modules directory to node_modules.bundled
mv %{buildroot}/%{_prefix}/lib/node_modules/npm/node_modules \
   %{buildroot}/%{_prefix}/lib/node_modules/npm/node_modules.bundled

# Recreate all the symlinks
mkdir -p %{buildroot}/%{_prefix}/lib/node_modules/npm/node_modules
FILES=%{buildroot}/%{_prefix}/lib/node_modules/npm/node_modules.bundled/*
for f in $FILES
do
  module=`basename $f`
  ln -s ../node_modules.bundled/$module %{buildroot}%{_prefix}/lib/node_modules/npm/node_modules/$module
done

# install NPM docs to mandir
mkdir -p %{buildroot}%{_mandir} \
         %{buildroot}%{_pkgdocdir}/npm

cp -pr deps/npm/man/* %{buildroot}%{_mandir}/
rm -rf %{buildroot}%{_prefix}/lib/node_modules/npm/man
ln -sf %{_mandir}  %{buildroot}%{_prefix}/lib/node_modules/npm/man

# Install Markdown and HTML documentation to %{_pkgdocdir}
cp -pr deps/npm/html deps/npm/doc %{buildroot}%{_pkgdocdir}/npm/
rm -rf %{buildroot}%{_prefix}/lib/node_modules/npm/html \
       %{buildroot}%{_prefix}/lib/node_modules/npm/doc

ln -sf %{_pkgdocdir} %{buildroot}%{_prefix}/lib/node_modules/npm/html
ln -sf %{_pkgdocdir}/npm/html %{buildroot}%{_prefix}/lib/node_modules/npm/doc


%check
%{?scl:scl enable %{scl} devtoolset-7 - << \EOF}
set -ex
# Fail the build if the versions don't match
#%{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.node, '%{nodejs_version}')"
#%{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.v8, '%{v8_version}')"
#%{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.ares.replace(/-DEV$/, ''), '%{c_ares_version}')"
#%{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.http_parser, '%{http_parser_version}')"

# Ensure we have punycode and that the version matches
#%{buildroot}/%{_bindir}/node -e "require(\"assert\").equal(require(\"punycode\").version, '%{punycode_version}')"

# Ensure we have npm and that the version matches
NODE_PATH=%{buildroot}%{_prefix}/lib/node_modules %{buildroot}/%{_bindir}/node -e "require(\"assert\").equal(require(\"npm\").version, '%{npm_version}')"

# move test that fails to directory which we do not use to run tests
#mv test/parallel/test-v8-serdes.js test/known_issues

# eslint is not included -> test always fail
#mv test/parallel/test-eslint-* test/known_issues

#mv test/doctool/test-make-doc.js test/known_issues
#mv test/parallel/test-regress-GH-746.js test/known_issues

#python tools/test.py --mode=release --verbose \
#async-hooks doctool inspector message \
#parallel pseudo-tty sequential

#make test

%{?scl:EOF}

%files
%{_bindir}/node
%{_mandir}/man1/node.*
%dir %{_pkgdocdir}
%dir %{_prefix}/lib/node_modules
%dir %{_datadir}/node
%dir %{_datadir}/systemtap
%dir %{_datadir}/systemtap/tapset
%{_datadir}/systemtap/tapset/node.stp

%dir %{_prefix}/lib/dtrace
%{_prefix}/lib/dtrace/node.d

#%{_rpmconfigdir}/fileattrs/nodejs_native.attr
#%{_rpmconfigdir}/nodejs_native.req
%license LICENSE
%doc AUTHORS CHANGELOG.md COLLABORATOR_GUIDE.md GOVERNANCE.md README.md

%files devel
%if 0%{?with_debug} == 1
%{_bindir}/node_g
%endif
%{_includedir}/node
%{_datadir}/node/common.gypi
%{_pkgdocdir}/gdbinit
%{_pkgdocdir}/lldbinit
%{_pkgdocdir}/lldb_commands.py*

%files -n %{?scl_prefix}npm
%{_bindir}/npm
%{_bindir}/npx
%{_prefix}/lib/node_modules/npm
%ghost %{_sysconfdir}/npmrc
%ghost %{_sysconfdir}/npmignore
%doc %{_mandir}/man*/npm*
%doc %{_mandir}/man*/npx*
%doc %{_mandir}/man5/package.json.5*
%doc %{_mandir}/man5/package-lock.json.5*
%doc %{_mandir}/man7/removing-npm.7*
%doc %{_mandir}/man7/semver.7*


%files docs
%dir %{_pkgdocdir}
%{_pkgdocdir}/html
%{_pkgdocdir}/npm
%{_pkgdocdir}/npm/html
%{_pkgdocdir}/npm/doc


%changelog
* Wed Oct 31 2018 Zuzana Svetlikova <zsvetlik@redhat.com> - 10.10.0-2
- Resolves: RHBZ#1584252
- comment out native.req file to prevent conflict with other Node.js
- installations (rhbz#1637922)

* Fri Sep 14 2018 Zuzana Svetlikova <zsvetlik@redhat.com> - 10.10.0-1
- rebase to v10.10.0
- update patches for openssl
- TODO: remove useless comments, fix failing tests, update bundled provides

* Thu Jul 19 2018 Zuzana Svetlikova <zsvetlik@redhat.com> - 10.1.0-1
- Initial v10 packaging
- patch crypto/openssl 1.1.0 -> 1.0.2
- remove scl prefixes from bundled dependencies
- TODO: update patches and dependencies

* Tue Feb 06 2018 Zuzana Svetlikova <zsvtelik@redhat.com> - 8.9.4-2
- Resolves: RHBZ#1513560 #1542079
- fix outdated minizlib dependency in npm node_modules tree
- https://github.com/nodejs/node/pull/16509

* Mon Jan 15 2018 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.9.4-1
- Resolves: RHBZ#1513560
- rebase to LTS

* Wed Sep 27 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.6.0-1
- Resolves: RHBZ#1490389
- Update, v8.5.0 contains a CVE

* Thu Sep 21 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.5.0-1
- Resolves: RHBZ#1490389
- Update to latest version, bundle nghttp2

* Thu Aug 10 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.3.0-2
- Handle failing test in better manner
- run more tests

* Thu Aug 10 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.3.0-1
- Update to 8.3.0
- update V8 to 6.0
- update libuv to 1.13.1
- add bundled provides for npm modules
- enable aarch64 builds

* Mon Jul 24 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.2.1-1
- Update to 8.2.1
- update npm to 5.3.0, add npx command

* Wed Jul 12 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.1.4-1
- Security update (https://nodejs.org/en/blog/vulnerability/july-2017-security-releases/)
- Fixes RHBZ#1463132 and RHBZ#1469706

* Wed Jun 28 2017 Joe Orton <jorton@redhat.com> - 8.1.2-7
- disable debug build on aarch64

* Wed Jun 28 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.1.2-6
- Build aarm64 without icu
- switch to dts 7

* Tue Jun 27 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.1.2-5
- Switch to DTS

* Tue Jun 27 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.1.2-4
- Add %%BuildArch

* Sat Jun 24 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.1.2-3
- Patch CVE-2017-1000381

* Fri Jun 23 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.1.2-2
- some clean up after fedora

* Mon Jun 19 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 8.1.2-1
- Initial v8.x build, npm@5.0.3
- remove merged certs patch
- build with updated system openssl
- use fedora-style packaging, bundle npm and dependencies
- bootstrap is modularity conditional to bundle http-parser 
- missing from base-runtime/shared-userspace
- RHSCL 3.0 should be built for more arches

* Wed Jan 11 2017 Zuzana Svetlikova <zsvetlik@redhat.com> - 6.9.1-2
- Rebuild from zvetlik/rh-nodejs6
- newer releases have problems with debug
- add procps-ng for tests
- remove unused patches

* Thu Nov 03 2016 Zuzana Svetlikova <zsvetlik@redhat.com> - 6.9.1-1
- Update to 6.9.1

* Wed Oct 19 2016 Zuzana Svetlikova <zsvetlik@redhat.com> - 6.9.0-1
- update to v6.9.0 LTS

* Tue Oct 04 2016 Zuzana Svetlikova <zsvetlik@redhat.com> - 6.7.0-5
- Disable failing crypto tests

* Tue Oct 04 2016 Zuzana Svetlikova <zsvetlik@redhat.com> - 6.7.0-4
- Require openssl

* Tue Oct 04 2016 Zuzana Svetlikova <zsvetlik@redhat.com> - 6.7.0-2
- Build with shared openssl with EPEL7 patch

* Mon Oct 03 2016 Zuzana Svetlikova <zsvetlik@redhat.com> - 6.7.0-1
- Update to 6.7.0

* Wed Aug 31 2016 Zuzana Svetlikova <zsvetlik@redhat.com> - 6.5.0-1
- Update to 6.5.0, meanwhile built with bundled openssl
- update system-certs patch

* Wed Apr 06 2016 Tomas Hrcka <thrcka@redhat.com> - 4.4.2-1
- Rebase to latest upstream LTS release 4.4.2
- https://nodejs.org/en/blog/release/v4.4.1/

* Tue Apr 05 2016 Tomas Hrcka <thrcka@redhat.com> - 4.4.1-2
- Rebase to latest upstream LTS release 4.4.1
- https://nodejs.org/en/blog/release/v4.4.1/

* Thu Mar 17 2016 Tomas Hrcka <thrcka@redhat.com> - 4.4.0-1
- Rebase to latest upstream LTS release 4.4.0

* Tue Mar 01 2016 Tomas Hrcka <thrcka@redhat.com> - 4.3.0-5
- New upstream release 4.3.0
- https://nodejs.org/en/blog/release/v4.3.0/
- Build with bundled openssl, this will be reverted ASAP
- Unbundled http-parser

* Thu Jul 16 2015 Tomas Hrcka <thrcka@redhat.com> - 0.10.40-1
- Rebase to latest upstream release

* Wed Jul 01 2015 Tomas Hrcka <thrcka@redhat.com> - 0.10.39-1
- Rebase to latest upstream release

* Wed Mar 25 2015 Tomas Hrcka <thrcka@redhat.com> - 0.10.35-4
- Enable tests during build time

* Tue Mar 17 2015 Tomas Hrcka <thrcka@redhat.com> - 0.10.35-2
- Reflect dependency on specific ABI changes in v8
- RHBZ#1197110

* Wed Jan 07 2015 Tomas Hrcka <thrcka@redhat.com> - 0.10.35-1
- New upstream release 0.10.35

* Sun Feb 02 2014 Tomas Hrcka <thrcka@redhat.com> - 0.10.25-1
- New upstream release 0.10.25

* Tue Jan 14 2014 Tomas Hrcka <thrcka@redhat.com> - 0.10.24-1
- new upstream release 0.10.24

* Tue Nov 26 2013 Tomas Hrcka <thrcka@redhat.com> - 0.10.21-3
- rebuilt with v8314 collection

* Tue Nov 12 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.22-1
- new upstream release 0.10.22
  http://blog.nodejs.org/2013/11/12/node-v0-10-22-stable/

* Mon Oct 21 2013 Tomas Hrcka <thrcka@redhat.com> - 0.10.21-2
- Build with system wide c-ares

* Fri Oct 18 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.21-1
- new upstream release 0.10.21
  http://blog.nodejs.org/2013/10/18/node-v0-10-21-stable/
- resolves an undisclosed security vulnerability in the http module

* Tue Oct 01 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.20-1
- new upstream release 0.10.20
  http://blog.nodejs.org/2013/09/30/node-v0-10-20-stable/

* Wed Sep 25 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.19-1
- new upstream release 0.10.19
  http://blog.nodejs.org/2013/09/24/node-v0-10-19-stable/

* Fri Sep 06 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.18-1
- new upstream release 0.10.18
  http://blog.nodejs.org/2013/09/04/node-v0-10-18-stable/

* Tue Aug 27 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.17-1
- new upstream release 0.10.17
  http://blog.nodejs.org/2013/08/21/node-v0-10-17-stable/

* Sat Aug 17 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.16-1
- new upstream release 0.10.16
  http://blog.nodejs.org/2013/08/16/node-v0-10-16-stable/
- add v8-devel to -devel Requires
- restrict -devel Requires to the same architecture

* Wed Aug 14 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.14-3
- fix typo in _isa macro in v8 Requires

* Wed Aug 07 2013 Tomas Hrcka <thrcka@redhat.com> - 0.10.5-6
 - Remove badly licensed fonts in script instead of patch

* Thu Jul 25 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.14-1
- new upstream release 0.10.14
  http://blog.nodejs.org/2013/07/25/node-v0-10-14-stable/

* Wed Jul 10 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.13-1
- new upstream release 0.10.13
  http://blog.nodejs.org/2013/07/09/node-v0-10-13-stable/
- remove RPM macros, etc. now that they've migrated to nodejs-packaging

* Wed Jun 19 2013 Tomas Hrcka <thrcka@redhat.com> - 0.10.5-5
 - added patch to remove badly licensed web fonts

* Wed Jun 19 2013 Tomas Hrcka <thrcka@redhat.com> - 0.10.5-5
 - added patch to remove badly licensed web fonts

* Wed Jun 19 2013 Tomas Hrcka <thrcka@redhat.com> - 0.10.5-4
  - strip openssl from the tarball it contains prohibited code (RHBZ#967736)
  - patch makefile so it do not use bundled deps
  - new stripped tarball

* Wed Jun 19 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.12-1
- new upstream release 0.10.12
  http://blog.nodejs.org/2013/06/18/node-v0-10-12-stable/
- split off a -packaging subpackage with RPM macros, etc.
- build -docs as noarch
- copy mutiple version logic from nodejs-packaging SRPM for now

* Fri May 31 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.9-1
- new upstream release 0.10.9
  http://blog.nodejs.org/2013/05/30/node-v0-10-9-stable/

* Wed May 29 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.8-1
- new upstream release 0.10.8
  http://blog.nodejs.org/2013/05/24/node-v0-10-8-stable/

* Wed May 29 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.7-1
- new upstream release 0.10.7
  http://blog.nodejs.org/2013/05/17/node-v0-10-7-stable/
- strip openssl from the tarball; it contains prohibited code (RHBZ#967736)
- patch Makefile so we can just remove all bundled deps completely

* Wed May 15 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.6-1
- new upstream release 0.10.6
  http://blog.nodejs.org/2013/05/14/node-v0-10-6-stable/

* Tue May 14 2013 Tomas Hrcka <thrcka@redhat.com> - 0.10.5-3.1
 - updated to latest upstream stable release

* Mon May 06 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.5-3
- nodejs-fixdep: work properly when a package has no dependencies

* Mon Apr 29 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.5-2
- nodejs-symlink-deps: make it work when --check is used and just
  devDependencies exist

* Wed Apr 24 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.5-1
- new upstream release 0.10.5
  http://blog.nodejs.org/2013/04/23/node-v0-10-5-stable/

* Mon Apr 15 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.4-1
- new upstream release 0.10.4
  http://blog.nodejs.org/2013/04/11/node-v0-10-4-stable/
- drop dependency generator files not supported on EL6
- port nodejs_default_filter to EL6
- add nodejs_find_provides_and_requires macro to invoke dependency generator
- invoke the standard RPM provides and requires generators from the Node.js ones
- write native module Requires from nodejs.req
- change the c-ares-devel Requires in -devel to match the BuildRequires

* Tue Apr 09 2013 Stephen Gallagher <sgallagh@redhat.com> - 0.10.3-2.1
- Build against c-ares 1.9

* Mon Apr 08 2013 Stanislav Ochotnicky <sochotnicky@redhat.com> - 0.10.3-3
- Add support for software collections
- Move rpm macros and tooling to separate package
- add no-op macro to permit spec compatibility with EPEL

* Thu Apr 04 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.3-2
- nodejs-symlink-deps: symlink unconditionally in the buildroot

* Wed Apr 03 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.3-1
- new upstream release 0.10.3
  http://blog.nodejs.org/2013/04/03/node-v0-10-3-stable/
- nodejs-symlink-deps: only create symlink if target exists
- nodejs-symlink-deps: symlink devDependencies when --check is used

* Sun Mar 31 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.2-1
- new upstream release 0.10.2
  http://blog.nodejs.org/2013/03/28/node-v0-10-2-stable/
- remove %%nodejs_arches macro since it will only be useful if it is present in
  the redhat-rpm-config package
- add default filtering macro to remove unwanted Provides from native modules
- nodejs-symlink-deps now supports multiple modules in one SRPM properly
- nodejs-symlink-deps also now supports a --check argument that works in the
  current working directry instead of the buildroot

* Fri Mar 22 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.1-1
- new upstream release 0.10.1
  http://blog.nodejs.org/2013/03/21/node-v0-10-1-stable/

* Wed Mar 20 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.0-4
- fix escaping in dependency generator regular expressions (RHBZ#923941)

* Wed Mar 13 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.10.0-3
- add virtual ABI provides for node and v8 so binary module's deps break when
  binary compatibility is broken
- automatically add matching Requires to nodejs binary modules
- add %%nodejs_arches macro to future-proof ExcluseArch stanza in dependent
  packages

* Tue Mar 12 2013 Stephen Gallagher <sgallagh@redhat.com> - 0.10.0-2
- Fix up documentation subpackage

* Mon Mar 11 2013 Stephen Gallagher <sgallagh@redhat.com> - 0.10.0-1
- Update to stable 0.10.0 release
- https://raw.github.com/joyent/node/v0.10.0/ChangeLog

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.9.5-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Jan 22 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-10
- minor bugfixes to RPM magic
  - nodejs-symlink-deps: don't create an empty node_modules dir when a module
    has no dependencies
  - nodes-fixdep: support adding deps when none exist
- Add the full set of headers usually bundled with node as deps to nodejs-devel.
  This way `npm install` for native modules that assume the stuff bundled with
  node exists will usually "just work".
-move RPM magic to nodejs-devel as requested by FPC

* Sat Jan 12 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-9
- fix brown paper bag bug in requires generation script

* Thu Jan 10 2013 Stephen Gallagher <sgallagh@redhat.com> - 0.9.5-8
- Build debug binary and install it in the nodejs-devel subpackage

* Thu Jan 10 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-7
- don't use make install since it rebuilds everything

* Thu Jan 10 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-6
- add %%{?isa}, epoch to v8 deps

* Wed Jan 09 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-5
- add defines to match libuv (#892601)
- make v8 dependency explicit (and thus more accurate)
- add -g to $C(XX)FLAGS instead of patching configure to add it
- don't write pointless 'npm(foo) > 0' deps

* Sat Jan 05 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-4
- install development headers
- add nodejs_sitearch macro

* Wed Jan 02 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-3
- make nodejs-symlink-deps actually work

* Tue Jan 01 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-2
- provide nodejs-devel so modules can BuildRequire it (and be consistent
  with other interpreted languages in the distro)

* Tue Jan 01 2013 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.5-1
- new upstream release 0.9.5
- provide nodejs-devel for the moment
- fix minor bugs in RPM magic
- add nodejs_fixdep macro so packagers can easily adjust dependencies in
  package.json files

* Wed Dec 26 2012 T.C. Hollingsworth <tchollingsworth@gmail.com> - 0.9.4-1
- new upstream release 0.9.4
- system library patches are now upstream
- respect optflags
- include documentation in subpackage
- add RPM dependency generation and related magic
- guard libuv depedency so it always gets bumped when nodejs does
- add -devel subpackage with enough to make node-gyp happy

* Thu Dec 20 2012 Stephen Gallagher <sgallagh@redhat.com> - 0.9.3-9
- Drop requirement on openssl 1.0.1

* Wed Dec 19 2012 Dan Horák <dan[at]danny.cz> - 0.9.3-8
- set exclusive arch list to match v8

* Tue Dec 18 2012 Stephen Gallagher <sgallagh@redhat.com> - 0.9.3-7
- Add remaining changes from code review
- Remove unnecessary BuildRequires on findutils
- Remove %%clean section

* Fri Dec 14 2012 Stephen Gallagher <sgallagh@redhat.com> - 0.9.3-6
- Fixes from code review
- Fix executable permissions
- Correct the License field
- Build debuginfo properly

* Thu Dec 13 2012 Stephen Gallagher <sgallagh@redhat.com> - 0.9.3-5
- Return back to using the standard binary name
- Temporarily adding a conflict against the ham radio node package until they
  complete an agreed rename of their binary.

* Wed Nov 28 2012 Stephen Gallagher <sgallagh@redhat.com> - 0.9.3-4
- Rename binary and manpage to nodejs

* Mon Nov 19 2012 Stephen Gallagher <sgallagh@redhat.com> - 0.9.3-3
- Update to latest upstream development release 0.9.3
- Include upstreamed patches to unbundle dependent libraries

* Tue Oct 23 2012 Adrian Alves <alvesadrian@fedoraproject.org>  0.8.12-1
- Fixes and Patches suggested by Matthias Runge

* Mon Apr 09 2012 Adrian Alves <alvesadrian@fedoraproject.org> 0.6.5
- First build.
