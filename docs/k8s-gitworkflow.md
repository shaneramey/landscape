# Git Workflow

## Branches
Helm branches are used when deploying applications

One environment pulls only from one git branch

Jenkins not needed
One landscaper process per namespace

## Release milestones
Tags are specified on each issue

Starting in the 1.6 release the release team will use the following procedure to identify release blocking issues
Any issues listed in the v1.6 milestone will be considered release blocking. It is everyone's responsibility to move non blocking issues out of the v1.6 milestone. Items targeting 1.7 can be moved into the v1.7 milestone. milestones or the release will not ship

(from https://github.com/kubernetes/features/blob/master/release-1.6/release-1.6.md)

# Review process
(from https://github.com/kubernetes/charts/blob/f9ce327b86f1fac812f3013aa024e8c41fb802c6/README.md)
The following outlines the review procedure used by the Chart repository maintainers. Github labels are used to indicate state change during the review process.

AWAITING REVIEW - Initial triage which indicates that the PR is ready for review by the maintainers team. The CLA must be signed and e2e tests must pass in-order to move to this state
CHANGES NEEDED - Review completed by at least one maintainer and changes needed by contributor (explicit even when using the review feature of Github)
CODE REVIEWED - The chart structure has been reviewed and found to be satisfactory given the technical requirements (may happen in parallel to UX REVIEWED)
UX REVIEWED - The chart installation UX has been reviewed and found to be satisfactory. (may happen in parallel to CODE REVIEWED)
LGTM - Added ONLY once both UX/CODE reviewed are both present. Merge must be handled by someone OTHER than the maintainer that added the LGTM label. This label indicates that given a quick pass of the comments this change is ready to merge

