import { test } from "node:test";
import assert from "node:assert/strict";
import { apiErrorMessage } from "../src/utils/apiError.ts";

test("validation responses explain the offending selling-value field", () => {
    assert.equal(apiErrorMessage({detail:[{loc:["body","selling_prices_tenths","1119"],msg:"Input should be greater than or equal to 0"}]},422),
        "selling_prices_tenths → 1119: Input should be greater than or equal to 0");
});
test("domain and string errors remain readable", () => {
    assert.equal(apiErrorMessage({detail:{error:"Invalid squad"}},400),"Invalid squad");
    assert.equal(apiErrorMessage({detail:"Player not found"},404),"Player not found");
});
test("unexpected error bodies have a safe fallback", () => {
    assert.match(apiErrorMessage(null,503),/503/);
    assert.match(apiErrorMessage({detail:[null,{}]},422),/check your entries/i);
});
