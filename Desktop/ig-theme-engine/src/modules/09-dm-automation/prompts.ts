export const DM_AUTOMATION_SYSTEM = `You are a DM funnel specialist for Instagram theme pages.

KEY PRINCIPLES:
- DM triggers convert passive viewers into active leads
- Every CTA should offer genuine, specific value
- Keyword triggers must be simple (1 word, easy to type)
- The DM sequence should deliver value FIRST, then soft-sell
- Email capture happens in the value delivery, not as a gate
- Follow-up sequence: value → value → soft ask → value → offer`;

export function dmFlowPrompt(niche: string, triggerKeyword: string, valueOffer: string): string {
  return `Create a complete DM automation flow for a "${niche}" Instagram theme page.

Trigger keyword: "${triggerKeyword}"
Value offer: "${valueOffer}"

Return JSON:
{
  "triggerKeyword": "${triggerKeyword}",
  "flowName": "descriptive flow name",
  "steps": [
    {
      "stepNumber": 1,
      "delay": "immediate|Xm|Xh|Xd",
      "messageType": "text|image|link|question",
      "message": "exact message text",
      "purpose": "what this step achieves",
      "includesLink": false,
      "linkUrl": "",
      "capturesEmail": false
    }
  ],
  "emailCaptureStep": {
    "stepNumber": number,
    "method": "how email is captured",
    "incentive": "why they give their email"
  },
  "conversionGoal": "what the flow ultimately drives",
  "expectedConversionRate": "X%",
  "followUpSequence": [
    { "day": 1, "message": "follow-up message", "purpose": "why" }
  ]
}`;
}

export function leadMagnetPrompt(niche: string): string {
  return `Create 5 lead magnet ideas for a "${niche}" Instagram theme page.

Each lead magnet should:
- Be deliverable via DM or email link
- Take less than 2 hours to create
- Provide immediate, tangible value
- Naturally lead to a paid product

Return JSON:
{
  "leadMagnets": [
    {
      "name": "lead magnet name",
      "type": "checklist|template|guide|toolkit|quiz",
      "description": "what it contains",
      "dmKeyword": "trigger word",
      "creationTime": "estimated hours",
      "conversionPotential": "high|medium",
      "paidProductBridge": "what paid product this naturally leads to"
    }
  ]
}`;
}
