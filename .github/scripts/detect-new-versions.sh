#!/usr/bin/env bash
# ==============================================================================
# detect-new-versions.sh
#
# Detects newer versions of SapMachine and GardenLinux compared to the known
# versions stored in .github/known-versions/versions.json
#
# GardenLinux is tracked as a map of {major: latest_minor_version} so we can
# detect both new majors and new minor patch releases within a major.
# The minor version is used in Dockerfiles for reproducibility:
#   FROM ghcr.io/gardenlinux/gardenlinux:1592.18
#
# Outputs (as GitHub Actions outputs via $GITHUB_OUTPUT):
#   new_sm_versions   - JSON array of {major, version} objects for new SapMachine releases
#   new_gl_versions   - JSON array of {major, version} objects for new GardenLinux releases
#   has_new_versions  - "true" if any new version was detected
#   build_matrix      - JSON matrix of {sm_major, sm_version, gl_major, gl_version} combinations
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
KNOWN_VERSIONS_FILE="${REPO_ROOT}/.github/known-versions/versions.json"

# ---------------------------------------------------------------------------
# 1. Load known versions
# ---------------------------------------------------------------------------
echo "::group::Loading known versions"
if [[ ! -f "${KNOWN_VERSIONS_FILE}" ]]; then
  echo "ERROR: ${KNOWN_VERSIONS_FILE} not found"
  exit 1
fi
cat "${KNOWN_VERSIONS_FILE}"
echo ""
echo "::endgroup::"

#KNOWN_SM_MAJORS=$(jq -r '.sapmachine | keys[]' "${KNOWN_VERSIONS_FILE}")

# ---------------------------------------------------------------------------
# 2. Fetch current SapMachine GA versions
# ---------------------------------------------------------------------------
echo "::group::Fetching SapMachine releases"
SM_JSON=$(curl -fsSL "https://sapmachine.io/assets/data/sapmachine-releases-latest.json")

# Extract GA (non-ea) releases. For each, get the major version and the full
# version from the first release tag.  Tag format: "sapmachine-<version>"
declare -A CURRENT_SM_VERSIONS
for key in $(echo "${SM_JSON}" | jq -r 'to_entries[] | select(.value.ea == false) | .key'); do
  major="${key}"  # e.g. "17", "21", "25", "26"
  tag=$(echo "${SM_JSON}" | jq -r --arg k "${key}" '.[$k].releases[0].tag')
  # tag is like "sapmachine-17.0.18" or "sapmachine-25.0.2" or "sapmachine-26"
  version="${tag#sapmachine-}"
  CURRENT_SM_VERSIONS["${major}"]="${version}"
  echo "  SapMachine ${major} (GA): ${version}"
done
echo "::endgroup::"

# ---------------------------------------------------------------------------
# 3. Fetch current active GardenLinux minor versions (latest per major)
# ---------------------------------------------------------------------------
echo "::group::Fetching GardenLinux active minor versions"
# Use the glrd container with JSON output to get all active minor releases,
# then extract the latest (highest) minor version per major.
# TODO: we can improve this part: https://github.com/gardenlinux/glrd/issues/20
GL_JSON=$(docker run --rm ghcr.io/gardenlinux/glrd "glrd --active --type minor --output-format json" 2>/dev/null || echo '{"releases":[]}')

# Build a map: gl_major → latest minor version string (e.g. "1592" → "1592.18")
# For versions < 2017: format is major.minor (e.g. 1592.18)
# For versions >= 2017: format is major.minor.patch (e.g. 2017.0.0)
declare -A CURRENT_GL_VERSIONS
if [[ "$(echo "${GL_JSON}" | jq '.releases | length')" -gt 0 ]]; then
  # Group by major, take the one with the highest minor (and patch) per major
  while IFS='|' read -r gl_major gl_minor_ver; do
    CURRENT_GL_VERSIONS["${gl_major}"]="${gl_minor_ver}"
    echo "  GardenLinux ${gl_major} latest minor: ${gl_minor_ver}"
  done < <(echo "${GL_JSON}" | jq -r '
    [.releases[] | {
      major: (.version.major | tostring),
      minor: .version.minor,
      patch: (.version.patch // null),
      version_str: (
        if .version.patch != null then
          "\(.version.major).\(.version.minor).\(.version.patch)"
        else
          "\(.version.major).\(.version.minor)"
        end
      )
    }]
    | group_by(.major)
    | map(sort_by(.minor, .patch) | last)
    | .[]
    | "\(.major)|\(.version_str)"
  ')
else
  echo "  WARNING: Could not fetch GardenLinux versions from glrd container."
  echo "  Falling back to known versions only."
  # Load known versions as fallback
  while IFS='=' read -r gl_major gl_ver; do
    CURRENT_GL_VERSIONS["${gl_major}"]="${gl_ver}"
  done < <(jq -r '.gardenlinux | to_entries[] | "\(.key)=\(.value)"' "${KNOWN_VERSIONS_FILE}")
fi
echo "::endgroup::"

# ---------------------------------------------------------------------------
# 4. Determine new SapMachine versions
# ---------------------------------------------------------------------------
echo "::group::Detecting new SapMachine versions"
declare -a NEW_SM_ITEMS=()  # each item: "major:version"

for major in "${!CURRENT_SM_VERSIONS[@]}"; do
  current_ver="${CURRENT_SM_VERSIONS[$major]}"
  known_ver=$(jq -r --arg m "${major}" '.sapmachine[$m] // ""' "${KNOWN_VERSIONS_FILE}")

  if [[ -z "${known_ver}" ]]; then
    echo "  NEW SapMachine major ${major}: ${current_ver} (not previously tracked)"
    NEW_SM_ITEMS+=("${major}:${current_ver}")
  elif [[ "${current_ver}" != "${known_ver}" ]]; then
    echo "  UPDATED SapMachine ${major}: ${known_ver} -> ${current_ver}"
    NEW_SM_ITEMS+=("${major}:${current_ver}")
  else
    echo "  SapMachine ${major}: ${current_ver} (unchanged)"
  fi
done
echo "::endgroup::"

# ---------------------------------------------------------------------------
# 5. Determine new GardenLinux versions (new major or updated minor)
# ---------------------------------------------------------------------------
echo "::group::Detecting new GardenLinux versions"
declare -a NEW_GL_ITEMS=()  # each item: "major:minor_version"

for gl_major in "${!CURRENT_GL_VERSIONS[@]}"; do
  current_minor="${CURRENT_GL_VERSIONS[$gl_major]}"
  known_minor=$(jq -r --arg m "${gl_major}" '.gardenlinux[$m] // ""' "${KNOWN_VERSIONS_FILE}")

  if [[ -z "${known_minor}" ]]; then
    echo "  NEW GardenLinux major ${gl_major}: ${current_minor} (not previously tracked)"
    NEW_GL_ITEMS+=("${gl_major}:${current_minor}")
  elif [[ "${current_minor}" != "${known_minor}" ]]; then
    echo "  UPDATED GardenLinux ${gl_major}: ${known_minor} -> ${current_minor}"
    NEW_GL_ITEMS+=("${gl_major}:${current_minor}")
  else
    echo "  GardenLinux ${gl_major}: ${current_minor} (unchanged)"
  fi
done
echo "::endgroup::"

# ---------------------------------------------------------------------------
# 6. Build the matrix of (sm_major, sm_version, gl_major, gl_version) combos
# ---------------------------------------------------------------------------
echo "::group::Building matrix"

# Use ONLY the current versions from sources — not the known file.
# This ensures stale versions (no longer active) never appear in the matrix.
# shellcheck disable=SC2034
declare -n ALL_SM_VERSIONS=CURRENT_SM_VERSIONS
# shellcheck disable=SC2034
declare -n ALL_GL_VERSIONS=CURRENT_GL_VERSIONS

MATRIX_JSON="[]"

has_new_sm=$( [[ ${#NEW_SM_ITEMS[@]} -gt 0 ]] && echo "true" || echo "false" )
has_new_gl=$( [[ ${#NEW_GL_ITEMS[@]} -gt 0 ]] && echo "true" || echo "false" )

if [[ "${has_new_sm}" == "true" && "${has_new_gl}" == "true" ]]; then
  # Both new → full cross-product of ALL SM × ALL GL
  echo "  Both SapMachine and GardenLinux have new versions → full rebuild"
  for sm_major in "${!ALL_SM_VERSIONS[@]}"; do
    sm_ver="${ALL_SM_VERSIONS[$sm_major]}"
    for gl_major in "${!ALL_GL_VERSIONS[@]}"; do
      gl_ver="${ALL_GL_VERSIONS[$gl_major]}"
      MATRIX_JSON=$(echo "${MATRIX_JSON}" | jq \
        --arg sm "$sm_major" --arg sv "$sm_ver" --arg gm "$gl_major" --arg gv "$gl_ver" \
        '. + [{"sm_major": $sm, "sm_version": $sv, "gl_major": $gm, "gl_version": $gv}]')
    done
  done

elif [[ "${has_new_sm}" == "true" ]]; then
  # Only new SM versions → new SM × ALL GL
  echo "  Only SapMachine has new versions → new SM × all GL"
  for item in "${NEW_SM_ITEMS[@]}"; do
    sm_major="${item%%:*}"
    sm_ver="${item#*:}"
    for gl_major in "${!ALL_GL_VERSIONS[@]}"; do
      gl_ver="${ALL_GL_VERSIONS[$gl_major]}"
      MATRIX_JSON=$(echo "${MATRIX_JSON}" | jq \
        --arg sm "$sm_major" --arg sv "$sm_ver" --arg gm "$gl_major" --arg gv "$gl_ver" \
        '. + [{"sm_major": $sm, "sm_version": $sv, "gl_major": $gm, "gl_version": $gv}]')
    done
  done

elif [[ "${has_new_gl}" == "true" ]]; then
  # Only new GL versions → ALL SM × new GL
  echo "  Only GardenLinux has new versions → all SM × new GL"
  for sm_major in "${!ALL_SM_VERSIONS[@]}"; do
    sm_ver="${ALL_SM_VERSIONS[$sm_major]}"
    for item in "${NEW_GL_ITEMS[@]}"; do
      gl_major="${item%%:*}"
      gl_ver="${item#*:}"
      MATRIX_JSON=$(echo "${MATRIX_JSON}" | jq \
        --arg sm "$sm_major" --arg sv "$sm_ver" --arg gm "$gl_major" --arg gv "$gl_ver" \
        '. + [{"sm_major": $sm, "sm_version": $sv, "gl_major": $gm, "gl_version": $gv}]')
    done
  done

else
  echo "  No new versions detected — nothing to build."
fi

MATRIX_COUNT=$(echo "${MATRIX_JSON}" | jq 'length')
echo "  Total build combinations: ${MATRIX_COUNT}"
echo "${MATRIX_JSON}" | jq '.'
echo "::endgroup::"

# ---------------------------------------------------------------------------
# 7. Produce outputs
# ---------------------------------------------------------------------------
HAS_NEW="false"
if [[ "${has_new_sm}" == "true" || "${has_new_gl}" == "true" ]]; then
  HAS_NEW="true"
fi

# Build new_sm_versions JSON array
SM_OUT="[]"
if [[ ${#NEW_SM_ITEMS[@]} -gt 0 ]]; then
  for item in "${NEW_SM_ITEMS[@]}"; do
    major="${item%%:*}"
    ver="${item#*:}"
    SM_OUT=$(echo "${SM_OUT}" | jq --arg m "${major}" --arg v "${ver}" '. + [{"major": $m, "version": $v}]')
  done
fi

# Build new_gl_versions JSON array
GL_OUT="[]"
if [[ ${#NEW_GL_ITEMS[@]} -gt 0 ]]; then
  for item in "${NEW_GL_ITEMS[@]}"; do
    gl_major="${item%%:*}"
    gl_ver="${item#*:}"
    GL_OUT=$(echo "${GL_OUT}" | jq --arg m "${gl_major}" --arg v "${gl_ver}" '. + [{"major": $m, "version": $v}]')
  done
fi

# Build full current-state JSON maps (for overriding versions.json in Job 3)
ALL_SM_JSON='{}'
for major in "${!CURRENT_SM_VERSIONS[@]}"; do
  ver="${CURRENT_SM_VERSIONS[$major]}"
  ALL_SM_JSON=$(echo "${ALL_SM_JSON}" | jq -c --arg m "${major}" --arg v "${ver}" '.[$m] = $v')
done

ALL_GL_JSON='{}'
for gl_major in "${!CURRENT_GL_VERSIONS[@]}"; do
  gl_ver="${CURRENT_GL_VERSIONS[$gl_major]}"
  ALL_GL_JSON=$(echo "${ALL_GL_JSON}" | jq -c --arg m "${gl_major}" --arg v "${gl_ver}" '.[$m] = $v')
done

# Write to GITHUB_OUTPUT – all JSON values MUST be compact (single-line)
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "has_new_versions=${HAS_NEW}"
    echo "new_sm_versions=$(echo "${SM_OUT}" | jq -c '.')"
    echo "new_gl_versions=$(echo "${GL_OUT}" | jq -c '.')"
    echo "build_matrix=$(echo "${MATRIX_JSON}" | jq -c '.')"
    echo "all_sm_versions=$(echo "${ALL_SM_JSON}" | jq -c '.')"
    echo "all_gl_versions=$(echo "${ALL_GL_JSON}" | jq -c '.')"
  } >> "${GITHUB_OUTPUT}"
else
  # For local testing
  echo ""
  echo "===== OUTPUTS ====="
  echo "has_new_versions=${HAS_NEW}"
  echo "new_sm_versions=${SM_OUT}"
  echo "new_gl_versions=${GL_OUT}"
  echo "build_matrix=${MATRIX_JSON}"
  echo "all_sm_versions=${ALL_SM_JSON}"
  echo "all_gl_versions=${ALL_GL_JSON}"
fi

# ---------------------------------------------------------------------------
# 8. Override the known versions file with current data from sources
#    This completely replaces the file – stale versions (e.g. a GL major
#    that is no longer active, or an SM version that was removed) are dropped.
# ---------------------------------------------------------------------------
echo "::group::Overriding known versions file with current source data"

# Build fresh JSON from CURRENT_SM_VERSIONS and CURRENT_GL_VERSIONS only
FRESH_JSON='{"sapmachine": {}, "gardenlinux": {}}'

for major in "${!CURRENT_SM_VERSIONS[@]}"; do
  ver="${CURRENT_SM_VERSIONS[$major]}"
  FRESH_JSON=$(echo "${FRESH_JSON}" | jq --arg m "${major}" --arg v "${ver}" '.sapmachine[$m] = $v')
done

for gl_major in "${!CURRENT_GL_VERSIONS[@]}"; do
  gl_ver="${CURRENT_GL_VERSIONS[$gl_major]}"
  FRESH_JSON=$(echo "${FRESH_JSON}" | jq --arg m "${gl_major}" --arg v "${gl_ver}" '.gardenlinux[$m] = $v')
done

echo "${FRESH_JSON}" | jq '.' > "${KNOWN_VERSIONS_FILE}"
echo "Overwritten ${KNOWN_VERSIONS_FILE} with current source data:"
cat "${KNOWN_VERSIONS_FILE}"
echo "::endgroup::"
