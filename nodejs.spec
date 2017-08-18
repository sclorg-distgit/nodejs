%{?scl:%scl_package nodejs}
%{!?scl:%global pkg_name %{name}}

%global with_debug 1

%{!?_with_bootstrap: %global bootstrap 1}

%{?!_pkgdocdir:%global _pkgdocdir %{_docdir}/%{pkg_name}-%{version}}

# ARM builds currently break on the Debug builds, so we'll just
# build the standard runtime until that gets sorted out.
%ifarch %{arm} aarch64 %{power64}
%global with_debug 1
%endif

# == Node.js Version ==
# Note: Fedora should only ship LTS versions of Node.js (currently expected
# to be major versions with even numbers). The odd-numbered versions are new
# feature releases that are only supported for nine months, which is shorter
# than a Fedora release lifecycle.
%global nodejs_major 8
%global nodejs_minor 3
%global nodejs_patch 0
%global nodejs_abi %{nodejs_major}.%{nodejs_minor}
%global nodejs_version %{nodejs_major}.%{nodejs_minor}.%{nodejs_patch}
%global nodejs_release 2

# == Bundled Dependency Versions ==
# v8 - from deps/v8/include/v8-version.h
%global v8_major 6
%global v8_minor 0
%global v8_build 286
%global v8_patch 52
# V8 presently breaks ABI at least every x.y release while never bumping SONAME
%global v8_abi %{v8_major}.%{v8_minor}
%global v8_version %{v8_major}.%{v8_minor}.%{v8_build}.%{v8_patch}

# c-ares - from deps/cares/include/ares_version.h
%global c_ares_major 1
%global c_ares_minor 10
%global c_ares_patch 1
%global c_ares_version %{c_ares_major}.%{c_ares_minor}.%{c_ares_patch}

# http-parser - from deps/http_parser/http_parser.h
%global http_parser_major 2
%global http_parser_minor 7
%global http_parser_patch 0
%global http_parser_version %{http_parser_major}.%{http_parser_minor}.%{http_parser_patch}

# libuv - from deps/uv/include/uv-version/h
%global libuv_major 1
%global libuv_minor 13
%global libuv_patch 1
%global libuv_version %{libuv_major}.%{libuv_minor}.%{libuv_patch}

# punycode - from lib/punycode.js
# Note: this was merged into the mainline since 0.6.x
# Note: this will be unmerged in v7 or v8
%global punycode_major 2
%global punycode_minor 0
%global punycode_patch 0
%global punycode_version %{punycode_major}.%{punycode_minor}.%{punycode_patch}

# npm - from deps/npm/package.json
%global npm_major 5
%global npm_minor 3
%global npm_patch 0
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
Release: %{nodejs_release}%{?dist}
Summary: JavaScript runtime
License: MIT and ASL 2.0 and ISC and BSD
Group: Development/Languages
URL: http://nodejs.org/

#BuildArch: %{nodejs_arches}
#ExclusiveArch: %{nodejs_arches}

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
Patch1: 0001-Disable-running-gyp-files-for-bundled-deps.patch

# Disable tests that are failing
# https://github.com/nodejs/help/issues/687
#Patch2: 0001-Disable-failed-tests.patch

%{?scl:Requires: %{scl}-runtime}
%{?scl:BuildRequires: %{scl}-runtime}
BuildRequires: python-devel
#BuildRequires: libicu-devel
BuildRequires: zlib-devel
BuildRequires: devtoolset-7-gcc
BuildRequires: devtoolset-7-gcc-c++
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

# Make sure we keep NPM up to date when we update Node.js
Requires: %{?scl_prefix}npm = %{npm_version}-%{npm_release}%{?dist}

%description
Node.js is a platform built on Chrome's JavaScript runtime
for easily building fast, scalable network applications.
Node.js uses an event-driven, non-blocking I/O model that
makes it lightweight and efficient, perfect for data-intensive
real-time applications that run across distributed devices.


%package devel
Summary: JavaScript runtime - development headers
Group: Development/Languages
Requires: %{?scl_prefix}%{pkg_name}%{?_isa} = %{nodejs_version}-%{nodejs_release}%{?dist}
#Requires: %{?scl_prefix}libuv-devel%{?_isa}
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
Release: %{npm_release}%{?dist}

# We used to ship npm separately, but it is so tightly integrated with Node.js
# (and expected to be present on all Node.js systems) that we ship it bundled
# now.
Provides: %{?scl_prefix}npm = %{npm_version}
Requires: %{?scl_prefix}nodejs = %{nodejs_version}-%{nodejs_release}%{?dist}

# Do not add epoch to the virtual NPM provides or it will break
# the automatic dependency-generation script.
Provides: %{?scl_prefix}npm(npm) = %{npm_version}

# Shipping each npm dependency as rpm is not very handy, so we bundle it now.
# However we still need to provide them in case there is a CVE
Provides: bundled(%{scl_prefix}nodejs-abbrev) = 1.0.9
Provides: bundled(%{scl_prefix}nodejs-ansi-regex) = 2.0.0
Provides: bundled(%{scl_prefix}nodejs-ansi-styles) = 2.2.1
Provides: bundled(%{scl_prefix}nodejs-ansicolors) = 0.3.2
Provides: bundled(%{scl_prefix}nodejs-ansistyles) = 0.1.3
Provides: bundled(%{scl_prefix}nodejs-aproba) = 1.0.4
Provides: bundled(%{scl_prefix}nodejs-archy) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-are-we-there-yet) = 1.1.2
Provides: bundled(%{scl_prefix}nodejs-array-index) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-asap) = 2.0.5
Provides: bundled(%{scl_prefix}nodejs-asn1) = 0.2.3
Provides: bundled(%{scl_prefix}nodejs-assert-plus) = 0.2.0
Provides: bundled(%{scl_prefix}nodejs-assert-plus) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-asynckit) = 0.4.0
Provides: bundled(%{scl_prefix}nodejs-aws-sign2) = 0.6.0
Provides: bundled(%{scl_prefix}nodejs-aws4) = 1.4.1
Provides: bundled(%{scl_prefix}nodejs-balanced-match) = 0.4.2
Provides: bundled(%{scl_prefix}nodejs-bcrypt-pbkdf) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-bl) = 1.1.2
Provides: bundled(%{scl_prefix}nodejs-block-stream) = 0.0.8
Provides: bundled(%{scl_prefix}nodejs-boom) = 2.10.1
Provides: bundled(%{scl_prefix}nodejs-brace-expansion) = 1.1.6
Provides: bundled(%{scl_prefix}nodejs-buffer-shims) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-builtin-modules) = 1.1.1
Provides: bundled(%{scl_prefix}nodejs-builtins) = 0.0.7
Provides: bundled(%{scl_prefix}nodejs-caseless) = 0.11.0
Provides: bundled(%{scl_prefix}nodejs-chalk) = 1.1.3
Provides: bundled(%{scl_prefix}nodejs-chownr) = 1.0.1
Provides: bundled(%{scl_prefix}nodejs-clone) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-cmd-shim) = 2.0.2
Provides: bundled(%{scl_prefix}nodejs-code-point-at) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-columnify) = 1.5.4
Provides: bundled(%{scl_prefix}nodejs-combined-stream) = 1.0.5
Provides: bundled(%{scl_prefix}nodejs-commander) = 2.9.0
Provides: bundled(%{scl_prefix}nodejs-concat-map) = 0.0.1
Provides: bundled(%{scl_prefix}nodejs-concat-stream) = 1.5.2
Provides: bundled(%{scl_prefix}nodejs-config-chain) = 1.1.11
Provides: bundled(%{scl_prefix}nodejs-console-control-strings) = 1.1.0
Provides: bundled(%{scl_prefix}nodejs-core-util-is) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-cryptiles) = 2.0.5
Provides: bundled(%{scl_prefix}nodejs-d) = 0.1.1
Provides: bundled(%{scl_prefix}nodejs-dashdash) = 1.14.0
Provides: bundled(%{scl_prefix}nodejs-debug) = 2.2.0
Provides: bundled(%{scl_prefix}nodejs-debuglog) = 1.0.1
Provides: bundled(%{scl_prefix}nodejs-defaults) = 1.0.3
Provides: bundled(%{scl_prefix}nodejs-delayed-stream) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-delegates) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-dezalgo) = 1.0.3
Provides: bundled(%{scl_prefix}nodejs-ecc-jsbn) = 0.1.1
Provides: bundled(%{scl_prefix}nodejs-editor) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-es5-ext) = 0.10.12
Provides: bundled(%{scl_prefix}nodejs-es6-iterator) = 2.0.0
Provides: bundled(%{scl_prefix}nodejs-es6-symbol) = 3.1.0
Provides: bundled(%{scl_prefix}nodejs-escape-string-regexp) = 1.0.5
Provides: bundled(%{scl_prefix}nodejs-extend) = 3.0.0
Provides: bundled(%{scl_prefix}nodejs-extsprintf) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-forever-agent) = 0.6.1
Provides: bundled(%{scl_prefix}nodejs-form-data) = 2.0.0
Provides: bundled(%{scl_prefix}nodejs-fs-vacuum) = 1.2.9
Provides: bundled(%{scl_prefix}nodejs-fs-write-stream-atomic) = 1.0.8
Provides: bundled(%{scl_prefix}nodejs-fs.realpath) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-fstream-ignore) = 1.0.5
Provides: bundled(%{scl_prefix}nodejs-fstream-npm) = 1.2.0
Provides: bundled(%{scl_prefix}nodejs-fstream) = 1.0.10
Provides: bundled(%{scl_prefix}nodejs-gauge) = 2.6.0
Provides: bundled(%{scl_prefix}nodejs-generate-function) = 2.0.0
Provides: bundled(%{scl_prefix}nodejs-generate-object-property) = 1.2.0
Provides: bundled(%{scl_prefix}nodejs-getpass) = 0.1.6
Provides: bundled(%{scl_prefix}nodejs-glob) = 6.0.4
Provides: bundled(%{scl_prefix}nodejs-glob) = 7.1.0
Provides: bundled(%{scl_prefix}nodejs-graceful-fs) = 4.1.9
Provides: bundled(%{scl_prefix}nodejs-graceful-readlink) = 1.0.1
Provides: bundled(%{scl_prefix}nodejs-har-validator) = 2.0.6
Provides: bundled(%{scl_prefix}nodejs-has-ansi) = 2.0.0
Provides: bundled(%{scl_prefix}nodejs-has-color) = 0.1.7
Provides: bundled(%{scl_prefix}nodejs-has-unicode) = 2.0.1
Provides: bundled(%{scl_prefix}nodejs-hawk) = 3.1.3
Provides: bundled(%{scl_prefix}nodejs-hoek) = 2.16.3
Provides: bundled(%{scl_prefix}nodejs-hosted-git-info) = 2.1.5
Provides: bundled(%{scl_prefix}nodejs-http-signature) = 1.1.1
Provides: bundled(%{scl_prefix}nodejs-iferr) = 0.1.5
Provides: bundled(%{scl_prefix}nodejs-imurmurhash) = 0.1.4
Provides: bundled(%{scl_prefix}nodejs-inflight) = 1.0.5
Provides: bundled(%{scl_prefix}nodejs-inherits) = 2.0.3
Provides: bundled(%{scl_prefix}nodejs-ini) = 1.3.4
Provides: bundled(%{scl_prefix}nodejs-init-package-json) = 1.9.4
Provides: bundled(%{scl_prefix}nodejs-is-builtin-module) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-is-fullwidth-code-point) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-is-my-json-valid) = 2.15.0
Provides: bundled(%{scl_prefix}nodejs-is-property) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-is-typedarray) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-isarray) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-isexe) = 1.1.2
Provides: bundled(%{scl_prefix}nodejs-isstream) = 0.1.2
Provides: bundled(%{scl_prefix}nodejs-jju) = 1.3.0
Provides: bundled(%{scl_prefix}nodejs-jodid25519) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-jsbn) = 0.1.0
Provides: bundled(%{scl_prefix}nodejs-json-parse-helpfulerror) = 1.0.3
Provides: bundled(%{scl_prefix}nodejs-json-schema) = 0.2.3
Provides: bundled(%{scl_prefix}nodejs-json-stringify-safe) = 5.0.1
Provides: bundled(%{scl_prefix}nodejs-jsonpointer) = 4.0.0
Provides: bundled(%{scl_prefix}nodejs-jsprim) = 1.3.1
Provides: bundled(%{scl_prefix}nodejs-lockfile) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-lodash._baseindexof) = 3.1.0
Provides: bundled(%{scl_prefix}nodejs-lodash._baseuniq) = 4.6.0
Provides: bundled(%{scl_prefix}nodejs-lodash._bindcallback) = 3.0.1
Provides: bundled(%{scl_prefix}nodejs-lodash._cacheindexof) = 3.0.2
Provides: bundled(%{scl_prefix}nodejs-lodash._createcache) = 3.1.2
Provides: bundled(%{scl_prefix}nodejs-lodash._createset) = 4.0.3
Provides: bundled(%{scl_prefix}nodejs-lodash._getnative) = 3.9.1
Provides: bundled(%{scl_prefix}nodejs-lodash._root) = 3.0.1
Provides: bundled(%{scl_prefix}nodejs-lodash.clonedeep) = 4.5.0
Provides: bundled(%{scl_prefix}nodejs-lodash.restparam) = 3.6.1
Provides: bundled(%{scl_prefix}nodejs-lodash.union) = 4.6.0
Provides: bundled(%{scl_prefix}nodejs-lodash.uniq) = 4.5.0
Provides: bundled(%{scl_prefix}nodejs-lodash.without) = 4.4.0
Provides: bundled(%{scl_prefix}nodejs-mime-db) = 1.24.0
Provides: bundled(%{scl_prefix}nodejs-mime-types) = 2.1.12
Provides: bundled(%{scl_prefix}nodejs-minimatch) = 3.0.3
Provides: bundled(%{scl_prefix}nodejs-minimist) = 0.0.8
Provides: bundled(%{scl_prefix}nodejs-mkdirp) = 0.5.1
Provides: bundled(%{scl_prefix}nodejs-ms) = 0.7.1
Provides: bundled(%{scl_prefix}nodejs-mute-stream) = 0.0.5
Provides: bundled(%{scl_prefix}nodejs-node-gyp) = 3.4.0
Provides: bundled(%{scl_prefix}nodejs-node-uuid) = 1.4.7
Provides: bundled(%{scl_prefix}nodejs-nopt) = 3.0.6
Provides: bundled(%{scl_prefix}nodejs-normalize-git-url) = 3.0.2
Provides: bundled(%{scl_prefix}nodejs-normalize-package-data) = 2.3.5
Provides: bundled(%{scl_prefix}nodejs-npm-cache-filename) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-npm-install-checks) = 3.0.0
Provides: bundled(%{scl_prefix}nodejs-npm-package-arg) = 4.2.0
Provides: bundled(%{scl_prefix}nodejs-npm-registry-client) = 7.2.1
Provides: bundled(%{scl_prefix}nodejs-npm-user-validate) = 0.1.5
Provides: bundled(%{scl_prefix}nodejs-npm) = 3.10.10
Provides: bundled(%{scl_prefix}nodejs-npmlog) = 3.1.2
Provides: bundled(%{scl_prefix}nodejs-npmlog) = 4.0.0
Provides: bundled(%{scl_prefix}nodejs-number-is-nan) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-oauth-sign) = 0.8.2
Provides: bundled(%{scl_prefix}nodejs-object-assign) = 4.1.0
Provides: bundled(%{scl_prefix}nodejs-once) = 1.4.0
Provides: bundled(%{scl_prefix}nodejs-opener) = 1.4.2
Provides: bundled(%{scl_prefix}nodejs-os-homedir) = 1.0.1
Provides: bundled(%{scl_prefix}nodejs-os-tmpdir) = 1.0.1
Provides: bundled(%{scl_prefix}nodejs-osenv) = 0.1.3
Provides: bundled(%{scl_prefix}nodejs-path-array) = 1.0.1
Provides: bundled(%{scl_prefix}nodejs-path-is-absolute) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-path-is-absolute) = 1.0.1
Provides: bundled(%{scl_prefix}nodejs-path-is-inside) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-pinkie-promise) = 2.0.1
Provides: bundled(%{scl_prefix}nodejs-pinkie) = 2.0.4
Provides: bundled(%{scl_prefix}nodejs-process-nextick-args) = 1.0.7
Provides: bundled(%{scl_prefix}nodejs-promzard) = 0.3.0
Provides: bundled(%{scl_prefix}nodejs-proto-list) = 1.2.4
Provides: bundled(%{scl_prefix}nodejs-qs) = 6.2.1
Provides: bundled(%{scl_prefix}nodejs-read-cmd-shim) = 1.0.1
Provides: bundled(%{scl_prefix}nodejs-read-installed) = 4.0.3
Provides: bundled(%{scl_prefix}nodejs-read-package-json) = 2.0.4
Provides: bundled(%{scl_prefix}nodejs-read-package-tree) = 5.1.5
Provides: bundled(%{scl_prefix}nodejs-read) = 1.0.7
Provides: bundled(%{scl_prefix}nodejs-readable-stream) = 2.0.6
Provides: bundled(%{scl_prefix}nodejs-readable-stream) = 2.1.5
Provides: bundled(%{scl_prefix}nodejs-readdir-scoped-modules) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-realize-package-specifier) = 3.0.3
Provides: bundled(%{scl_prefix}nodejs-request) = 2.75.0
Provides: bundled(%{scl_prefix}nodejs-retry) = 0.10.0
Provides: bundled(%{scl_prefix}nodejs-rimraf) = 2.5.4
Provides: bundled(%{scl_prefix}nodejs-semver) = 5.3.0
Provides: bundled(%{scl_prefix}nodejs-set-blocking) = 2.0.0
Provides: bundled(%{scl_prefix}nodejs-sha) = 2.0.1
Provides: bundled(%{scl_prefix}nodejs-signal-exit) = 3.0.0
Provides: bundled(%{scl_prefix}nodejs-slide) = 1.1.6
Provides: bundled(%{scl_prefix}nodejs-sntp) = 1.0.9
Provides: bundled(%{scl_prefix}nodejs-sorted-object) = 2.0.1
Provides: bundled(%{scl_prefix}nodejs-spdx-correct) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-spdx-exceptions) = 1.0.4
Provides: bundled(%{scl_prefix}nodejs-spdx-expression-parse) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-spdx-license-ids) = 1.2.0
Provides: bundled(%{scl_prefix}nodejs-sshpk) = 1.10.1
Provides: bundled(%{scl_prefix}nodejs-string-width) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-string_decoder) = 0.10.31
Provides: bundled(%{scl_prefix}nodejs-stringstream) = 0.0.5
Provides: bundled(%{scl_prefix}nodejs-strip-ansi) = 3.0.1
Provides: bundled(%{scl_prefix}nodejs-supports-color) = 2.0.0
Provides: bundled(%{scl_prefix}nodejs-tar) = 2.2.1
Provides: bundled(%{scl_prefix}nodejs-text-table) = 0.2.0
Provides: bundled(%{scl_prefix}nodejs-tough-cookie) = 2.3.1
Provides: bundled(%{scl_prefix}nodejs-tunnel-agent) = 0.4.3
Provides: bundled(%{scl_prefix}nodejs-tweetnacl) = 0.14.3
Provides: bundled(%{scl_prefix}nodejs-typedarray) = 0.0.6
Provides: bundled(%{scl_prefix}nodejs-uid-number) = 0.0.6
Provides: bundled(%{scl_prefix}nodejs-umask) = 1.1.0
Provides: bundled(%{scl_prefix}nodejs-unique-filename) = 1.1.0
Provides: bundled(%{scl_prefix}nodejs-unique-slug) = 2.0.0
Provides: bundled(%{scl_prefix}nodejs-unpipe) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-util-deprecate) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-util-extend) = 1.0.3
Provides: bundled(%{scl_prefix}nodejs-validate-npm-package-license) = 3.0.1
Provides: bundled(%{scl_prefix}nodejs-validate-npm-package-name) = 2.2.2
Provides: bundled(%{scl_prefix}nodejs-verror) = 1.3.6
Provides: bundled(%{scl_prefix}nodejs-wcwidth) = 1.0.0
Provides: bundled(%{scl_prefix}nodejs-which) = 1.2.11
Provides: bundled(%{scl_prefix}nodejs-wide-align) = 1.1.0
Provides: bundled(%{scl_prefix}nodejs-wrappy) = 1.0.2
Provides: bundled(%{scl_prefix}nodejs-write-file-atomic) = 1.2.0
Provides: bundled(%{scl_prefix}nodejs-xtend) = 4.0.1

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
%patch1 -p1

# disable tests
#%patch2 -p1

rm -rf deps/zlib


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
           --openssl-use-def-ca-store
%else
./configure --prefix=%{_prefix} \
           --shared-openssl \
           --shared-zlib \
           --with-dtrace \
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
install -Dpm0644 %{SOURCE7} %{buildroot}%{_rpmconfigdir}/fileattrs/nodejs_native.attr
cat << EOF > %{buildroot}%{_rpmconfigdir}/nodejs_native.req
#!/bin/sh
echo 'nodejs(abi%{nodejs_major}) >= %nodejs_abi'
echo 'nodejs(v8-abi%{v8_major}) >= %v8_abi'
EOF
chmod 0755 %{buildroot}%{_rpmconfigdir}/nodejs_native.req

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
%{?scl:scl enable %{scl} - << \EOF}
set -ex
# Fail the build if the versions don't match
%{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.node, '%{nodejs_version}')"
%{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.v8, '%{v8_version}')"
%{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.ares.replace(/-DEV$/, ''), '%{c_ares_version}')"
%{buildroot}/%{_bindir}/node -e "require('assert').equal(process.versions.http_parser, '%{http_parser_version}')"

# Ensure we have punycode and that the version matches
%{buildroot}/%{_bindir}/node -e "require(\"assert\").equal(require(\"punycode\").version, '%{punycode_version}')"

# Ensure we have npm and that the version matches
NODE_PATH=%{buildroot}%{_prefix}/lib/node_modules %{buildroot}/%{_bindir}/node -e "require(\"assert\").equal(require(\"npm\").version, '%{npm_version}')"

# move test that fails to directory which we do not use to run tests
mv test/parallel/test-v8-serdes.js test/known_issues

python tools/test.py --mode=release --verbose \
async-hooks doctool inspector message \
parallel pseudo-tty sequential || :
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

%{_rpmconfigdir}/fileattrs/nodejs_native.attr
%{_rpmconfigdir}/nodejs_native.req
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
