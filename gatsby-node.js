/**
 * Implement Gatsby's Node APIs in this file.
 * See: https://www.gatsbyjs.org/docs/node-apis/
 */

const Promise = require(`bluebird`)
const path = require(`path`)

// Implement the Gatsby API “createPages”. This is
// called after the Gatsby bootstrap is finished so you have
// access to any information necessary to programmatically
// create pages.

exports.createPages = ({ graphql, actions }) => {
  const { createPage } = actions
  return graphql(`
    {
      allSection {
        edges {
          node {
            id
            slug
          }
        }
      }
    }
  `).then(result => {
    if (result.errors) {
      throw new Error(result.errors)
    }
    const pageTemplate = path.resolve(`src/templates/sectionPage.js`)
    result.data.allSection.edges.map(edge => {
      const section = edge.node
      createPage({
        path: `/${section.slug}/`,
        component: pageTemplate,
        context: {
          id: section.id,
        }
      })
    })
  })
}
