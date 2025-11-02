.PHONY: validate
validate:
	pyshacl -s schemas/uofa.shacl.ttl -df json-ld -d examples/mock-medical-minimal.jsonld -f human
	pyshacl -s schemas/uofa.shacl.ttl -df json-ld -d examples/mock-aero-complete.jsonld -f human
	pyshacl -s schemas/uofa.shacl.ttl -df json-ld -d examples/mock-self-contained-complete.jsonld  -f human

