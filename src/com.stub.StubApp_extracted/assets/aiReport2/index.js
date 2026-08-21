const { createApp, ref, onMounted } = Vue;

const App = {
  components: {
    SeptKatex,
  },
  setup() {
    let report = ref();
    let option = ref();
    let noEchart = ref(false);
    let details = ref([]);
    let katexStr = ref("");
    let isSelect = ref(false);
    let katexTest = ref(
      "包$$C\\colon \\frac{x^{2}}{a^{2}}+\\frac{y^{2}}{b^{2}}=1\\left(a\\gt  b\\gt  0\\right)$$ 含行内公式 $E=mc^2$ 和块级公式 $$\\int_a^b f(x)dx$$,"
    );
    onMounted(function () {
      document.addEventListener("SeptJSBridageListener", function (event) {
        console.log(
          "weblog ---ReportResultListener" +
            JSON.stringify(event.detail.message)
        );
        var sk = document.getElementById("skeleton-id");
        if (sk) {
          sk.style.display = "none";
        }
        console.log("ddddddd", JSON.stringify(event.detail.message));
        let m = JSON.parse(JSON.stringify(event.detail.message.detail)) || [];
        katexStr.value = m[0].Content;
        isSelect.value = m[0].isSelect=="true" ? true : false;
      });
    });

    return {
      report,
      noEchart,
      details,
      katexTest,
      katexStr,
      isSelect,
    };
  },
};

createApp(App).mount("#app");
