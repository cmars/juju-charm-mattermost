package main

import (
	"encoding/json"
	"io/ioutil"
	"os"
)

func main() {
	f, err := os.Open("plan.yaml")
	if err != nil {
		panic(err)
	}
	buf, err := ioutil.ReadAll(f)
	if err != nil {
		panic(err)
	}
	err = json.NewEncoder(os.Stdout).Encode(map[string]interface{}{
		"url":  "cmars/mattermost-labeled-plan",
		"plan": string(buf),
	})
	if err != nil {
		panic(err)
	}
}
