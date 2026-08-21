
const SeptKatex = {
  props: {
    text: String,
    select: Boolean,
    fontsize:{
        type:Number,
        required:false,
        default:()=>13,
        },
    delimiters: {
        type: Array,
        default: () => [
            { left: '$$', right: '$$', display: false },
            { left: '$', right: '$', display: false }
        ]
        }
  },
  setup(props) {
    Vue.onMounted(() => {
        if (window.location.host.includes("7net.cc")) {
            console.log = function () {};
            console.info = function () {};
        }else{
        }
        console.log('CDN: 组件挂载完毕',props.text);
    });

     // 构建正则表达式
    const buildRegex = (delimiters) => {
        const patterns = delimiters.map(d => {
        const left = escapeRegExp(d.left);
        const right = escapeRegExp(d.right);
        return `(${left}(.*?)${right})`;
        });
        return new RegExp(patterns.join('|'), 'g');
    }; 

    // 转义正则表达式特殊字符
    const escapeRegExp = (string) => {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

     // 处理文本片段
    const processText = (text) => {
        // console.log("ddfffffffffffxxx:",JSON.stringify(text))

//        text="$$升温$$|$$6.0\\sim9.0$$|$$\\mathrm{SiO}_2,\\ \\mathrm{Fe(OH)}_3,\\ \\mathrm{Al(OH)为之}$$"
        // text = text.replaceAll('$$',"$")
        // text = text.replace(/\$\$/g, '$');
        text = text.split('$$').join('$');
        const regex = buildRegex(props.delimiters);
        const segments = [];
        let lastIndex = 0;
        
        text.replace(regex, (match, p1, p2, p3, p4, offset) => {
        // 添加前面的普通文本
        if (offset > lastIndex) {
            segments.push({
            type: 'text',
            content: text.substring(lastIndex, offset)
            });
        }
        
        // 确定是哪个分隔符匹配的
        let formula = '';
        let displayMode = false;
        
        props.delimiters.forEach((d) => {
            if (match.startsWith(d.left) && match.endsWith(d.right)) {
            formula = match.slice(d.left.length, -d.right.length);
            displayMode = d.display;
            }
        });
        
        // 渲染公式
        try {
            const rendered = katex.renderToString(formula, {
            displayMode,
            strict:false,
            throwOnError: false
            });
            segments.push({
            type: 'formula',
            content: rendered
            });
        } catch (e) {
            console.error('KaTeX渲染错误:', e);
            segments.push({
            type: 'text',
            content: match
            });
        }
        
        lastIndex = offset + match.length;
        return match;
        });
        
        // 添加剩余文本
        if (lastIndex < text.length) {
        segments.push({
            type: 'text',
            content: text.substring(lastIndex)
        });
        }
        
        return segments;
    };
    
    const processedSegments = Vue.computed(() => processText(props.text));
    // const processedSegments = ref();
    const select = Vue.computed(() => props.select? '#2B6FF6' : 'black');

    return {processedSegments,select};
  },
  template: `
    <div>
      <template v-for="(segment, index) in processedSegments" :key="index">
        <span :style="{'fontSize':'13px', color: select}" v-if="segment.type === 'text'">{{ segment.content }}</span>
        <span :style="{'fontSize':'13px', color: select}" v-else v-html="segment.content"></span>
      </template>
    </div>
  `
};
