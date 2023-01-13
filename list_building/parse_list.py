import re, json

tcodes_md_file = "t-codes.md"
tcodes_file = "../tcodes.json"

##### Costruisce lista da t-codes.md ##########################################

def print_result(code, descr):
	item = {
		"code": code.replace("/n", "").replace("/N", "").upper(),
		"descr": descr.replace(":", "").strip(),
		"keywords": descr.replace(":", "").strip()
	}
	return item

with open(tcodes_md_file, "r", encoding="utf-8") as file:
	codes_file_content = file.read()

codes = codes_file_content.splitlines()

parsed_codes = []

for code in codes:
	if (code.startswith("#")): continue
	if (code.strip() == ""): continue
	if (code.strip().startswith("--")): continue

	result = re.search('^-\s+`(.*)`\s*(.*)$', code)
	if (result):
		parsed_codes.append([result.group(1), result.group(2)])
	else:
		print("!!!!!!!", code)

parsed_codes.sort(key=lambda x: x[0])

result_json = []

for code in parsed_codes:
	result_json.append(print_result(code[0], code[1]))


##### Apre tcodes già estratti ################################################

with open(tcodes_file, "r") as file:
	existing_codes = json.loads(file.read())


##### Verifica se codici appena parsati sono già presenti in lista ############

for just_parsed in result_json:

	found_already_existing = [x for x in existing_codes if x['code'] == just_parsed['code']]
	if (len(found_already_existing) == 0):
		print(just_parsed)







# with open("tcodes.json", "w", encoding="utf-8") as file:
# 	file.write(json.dumps(result_json, indent=4))