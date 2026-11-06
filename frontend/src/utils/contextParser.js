/**
 * Wardrobe Context Rule Parser & State Manager
 * Parses user chatbot messages into structured outfit generation rules.
 */

export function parseContextRules(textInput, currentRules = {}) {
  const text = (textInput || '').toLowerCase();
  
  // 1. Detect Category & Item Exclusions
  const bagRegex = /no bag|no bags|no purses|no purse|no handbag|no handbags|no tote|no backpack|don't want bag|don't want bags|dont want bag|dont want bags|without bag|without bags|exclude bag|exclude bags|remove bag|remove bags|don't give me purse|don't give me bag|didn't give me purse|didn't give me bag|no purses\/bags|not want bag|not want bags|don't include bag|don't include bags/i;
  const accessoryRegex = /no accessory|no accessories|no jewellery|no jewelry|no watch|no watches|don't want accessory|don't want accessories|without accessory|without accessories|exclude accessory|exclude accessories|no jewel|no jewels|remove accessories/i;
  const outerwearRegex = /no outerwear|no jacket|no jackets|no coat|no coats|no blazer|no blazers|don't want jacket|don't want jackets|without jacket|without outerwear|exclude jacket|exclude outerwear/i;
  const footwearRegex = /no shoe|no shoes|no footwear|exclude footwear|no heels|heels off|sneakers only/i;

  let excludeBags = currentRules.excludeBags || false;
  let excludeAccessories = currentRules.excludeAccessories || false;
  let excludeOuterwear = currentRules.excludeOuterwear || false;
  let excludeFootwear = currentRules.excludeFootwear || false;

  if (bagRegex.test(text)) {
    excludeBags = true;
  }
  if (accessoryRegex.test(text)) {
    excludeAccessories = true;
  }
  if (outerwearRegex.test(text)) {
    excludeOuterwear = true;
  }
  if (footwearRegex.test(text)) {
    excludeFootwear = true;
  }

  // Allow resetting exclusions if user explicitly types "include bags" or "reset" or "clear" or "allow bags"
  if (/include bag|allow bag|reset bag|reset rule|clear rule|reset constraint|with bag|allow purse|with purse|allow accessories|include accessories/i.test(text)) {
    if (text.includes('bag') || text.includes('purse') || text.includes('reset') || text.includes('clear')) excludeBags = false;
    if (text.includes('accessory') || text.includes('jewel') || text.includes('reset') || text.includes('clear')) excludeAccessories = false;
    if (text.includes('jacket') || text.includes('outerwear') || text.includes('reset') || text.includes('clear')) excludeOuterwear = false;
    if (text.includes('shoe') || text.includes('footwear') || text.includes('heel') || text.includes('reset') || text.includes('clear')) excludeFootwear = false;
  }

  // 2. Extract general text-based exclusion keywords for flexible matching
  const dynamicExclusions = [...(currentRules.dynamicExclusions || [])];
  
  // Extract patterns like "no X", "don't want X", "without X", "exclude X"
  const exclusionMatches = text.matchAll(/(?:no|don't want|dont want|without|exclude|remove|don't give me|didn't give me)\s+([a-z0-9\s]+?)(?:on|for|in|\.|\,|$)/gi);
  for (const match of exclusionMatches) {
    const rawPhrase = match[1].trim();
    if (rawPhrase && rawPhrase.length > 2 && !['a', 'the', 'my', 'any'].includes(rawPhrase)) {
      if (!dynamicExclusions.includes(rawPhrase)) {
        dynamicExclusions.push(rawPhrase);
      }
    }
  }

  // 3. Detect Footwear Specific Request (e.g., "only want shoe", "only use shoe", "shoe with all outfits")
  let preferredFootwear = currentRules.preferredFootwear || null;
  const preferredShoeRegex = /only want shoe|only use shoe|shoe with all|shoe only|only shoe|prefer shoe|use shoe|want shoe/i;

  if (preferredShoeRegex.test(text)) {
    preferredFootwear = 'Shoe';
  } else if (/reset shoe|allow all shoes|clear shoe/i.test(text)) {
    preferredFootwear = null;
  }

  // 4. Build human readable list of active exclusions & preferences
  const activeExclusions = [];
  if (excludeBags) activeExclusions.push('👜 Bags & Purses');
  if (excludeAccessories) activeExclusions.push('💎 Accessories & Jewellery');
  if (excludeOuterwear) activeExclusions.push('🧥 Outerwear & Jackets');
  if (excludeFootwear) activeExclusions.push('👟 Footwear Constraints');
  if (preferredFootwear) activeExclusions.push(`👟 Preferred Footwear: ${preferredFootwear} (except Kurti/Ethnic)`);
  
  // Include any extra parsed phrases that aren't already represented
  dynamicExclusions.forEach(phrase => {
    if (!phrase.includes('bag') && !phrase.includes('purse') && !phrase.includes('accessory') && !phrase.includes('jacket') && !phrase.includes('shoe')) {
      activeExclusions.push(`🚫 ${phrase}`);
    }
  });

  // 5. Infer Routine & Preference
  let derivedRoutine = currentRules.defaultRoutine || 'Daily Look';
  let derivedPref = currentRules.stylePreference || 'stylish-trendy';

  if (text.includes('college') || text.includes('student') || text.includes('university') || text.includes('campus')) {
    derivedRoutine = 'Daily Look (Campus)';
  } else if (text.includes('office') || text.includes('work') || text.includes('corporate') || text.includes('professional')) {
    derivedRoutine = 'Work & Office';
  } else if (text.includes('party') || text.includes('nightout') || text.includes('club')) {
    derivedRoutine = 'Party / Night Out';
  }

  if (text.includes('minimal')) derivedPref = 'minimal';
  else if (text.includes('bold') || text.includes('party')) derivedPref = 'bold';
  else if (text.includes('classic') || text.includes('formal')) derivedPref = 'classic';
  else if (text.includes('trendy') || text.includes('stylish')) derivedPref = 'stylish-trendy';

  // Combine full context instruction history without duplicate entries
  const existingRules = currentRules.context_rules ? currentRules.context_rules.split('; ') : [];
  if (!existingRules.includes(textInput)) {
    existingRules.push(textInput);
  }
  const contextRulesText = existingRules.join('; ');

  return {
    ...currentRules,
    defaultRoutine: derivedRoutine,
    stylePreference: derivedPref,
    excludeBags,
    excludeAccessories,
    excludeOuterwear,
    excludeFootwear,
    preferredFootwear,
    dynamicExclusions,
    activeExclusions,
    userBio: textInput,
    context_rules: contextRulesText,
    lastUpdatedRule: textInput
  };
}
